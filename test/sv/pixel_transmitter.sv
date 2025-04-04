//`include "packet_builder.sv"
//`include "high_speed_transmitter.sv"
//`include "asynch_fifo.sv"
//`include "synchronization.sv"
//`include "apb_slave.sv"

module pixel_transmitter
  #(
    parameter FIFO_DEPTH = 8'd8,        //NUMBER OF REGISTER USED FOR SAVING DATA IN AFIFO
    parameter AFIFO_DW = 8'd65,         //WIDTH OF REGISTER IN AFIFO
    parameter AFIFO_AFULL_TH = 8'd2     //MINIMUM DIEFRWNCE BETWEEN READ AND WRITE POINTER FOR AFULL SIGNAL TO GO ACTIVE
  )
  (
    //GLOBAL SIGNALS
    input  logic              i_f_clk_ao,         //SYSTEM CLOCK
    input  logic              i_reset_fclk_n,     //ASYNC RESET ACTIVE LOW

    //APB IF
    input  logic [31:0]       i_paddr,            //APB ADDRESS BUS
    input  logic              i_psel,             //APB SEL
    input  logic              i_penable,          //APB ENABLE
    input  logic              i_pwrite,           //SIGNAL THAT INDICATES IF ITS APB WRITE(HIGH) 0R APB READ(LOW)
    input  logic [31:0]       i_pwdata,           //APB WRITE DATA
    output logic              o_pready,           //APB READY
    output logic [31:0]       o_prdata,           //APB READ DATA
    output logic              o_pslverr,          //APB SLAVE ERROR

    //HIGH-SPEED IF
    input  logic              i_txclkhs,          //HIGH-SPEED CLOCK
    input  logic              i_txreadyhs,        //HIGH-SPEED READY SIGNAL FOR DATA LANE
    output logic [7:0]        o_txdatahs,         //HIGH-SPEED DATA BUS
    output logic              o_txrequesths,      //HIGH-SPEED REQUEST FOR DATA LANE  
    output logic              o_txrequesths_clk,  //HIGH-SPEED REQUEST FOR CLK LANE

    //PIXEL INTERFACE
    input  logic              i_pi_fs_valid,      //SIGNAL THAT INDICATES FRAME START
    input  logic              i_pi_fe_valid,      //SIGNAL THAT INDICATES FRAME END
    input  logic              i_pi_ls_valid,      //SIGNAL THAT INDICATES LINE START
    input  logic              i_pi_le_valid,      //SIGNAL THAT INDICATES LINE END
    input  logic              i_pi_pxl_valid,     //SIGNAL THAT INDICATES VALID PIXEL DATA
    input  logic [63:0]       i_pi_pxl_data,      //PIXEL DATA BUS
    output logic              o_pi_pxl_ready,     //SIGNAL THAT INDICATES THAT PIXEL TRANSMITTER IS READY TO ACEPT DATA
    output logic              o_interrupt         //INTERRUPT PORT
  );

  //SIGNALS FOR CONNECING PACKET BUILDER WITH APB SLAVE
  logic [31:0] pxl_tx_fs_pckt;
  logic [31:0] pxl_tx_fe_pckt;
  logic [15:0] pxl_tx_long_pckt;

  //SOFTWARE SYNCH RESET
  logic soft_reset;
  logic soft_reset_hs;

  //INTERRUPT SIGNALS FROM DIFFERENT MODULES
  logic interrupt_pb;
  logic interrupt_hs;
  logic synch_interrupt_hs;

  //SIGNAL FOR CONNECTING PACKET BUILDER WITH SYNCRONIZATION SUB MODULE
  logic is_idle_packet_builder;

  //SIGNAL FOR CONNECTING WITH AFIFO WITH HS TRANSMITTER AND PACKET BUILDER SUB MODULES
  logic [64:0] wdata_fifo;
  logic [64:0] rdata_fifo;
  logic write_en;
  logic read_en;
  logic afull;
  logic empty;

  //SIGNAL FOR CONNECTING HS TRANSMITTER AND SYNCRONIZATION SUB MODULES
  logic reset_hsclk_n;
  logic is_idle_high_speed_transmitter;
  logic [7:0] hs_dl_reg_dly;
  logic [3:0] hs_clk_pre;
  logic [3:0] hs_clk_post;

  //SIGNALS FOR CONNECTING SYNCRONIZATION SUB MODULE AND APB SLAVE
  logic [15:0] hs_clk_dly;
  logic write_r;
  logic is_idle;

  //LOCAL PARAMETERS FOR INSTANCES OF SUB MODULE
  localparam PXL_WIDTH      = 8'd64;
  localparam STAGE_NUMBER   = 8'd3;
  localparam HS_DATA_WIDTH  = 8'd8;

  //PACKET BUILER SUB MODULE INSTANCE
  packet_builder
  #(
    .PXL_WIDTH(PXL_WIDTH),
    .AFIFO_DW(AFIFO_DW)
  )
  packet_builder_i
  (
    .i_f_clk_ao(i_f_clk_ao),
    .i_rst_fclk_n(i_reset_fclk_n),
    .i_pxl_tx_fs_pckt(pxl_tx_fs_pckt),
    .i_pxl_tx_fe_pckt(pxl_tx_fe_pckt),
    .i_pxl_tx_long_pckt(pxl_tx_long_pckt),
    .o_is_idle(is_idle_packet_builder),
    .i_pi_fs_valid(i_pi_fs_valid),
    .i_pi_fe_valid(i_pi_fe_valid),
    .i_pi_ls_valid(i_pi_ls_valid),
    .i_pi_le_valid(i_pi_le_valid),
    .i_pi_pxl_valid(i_pi_pxl_valid),
    .i_pi_pxl_data(i_pi_pxl_data),
    .o_pi_pxl_ready(o_pi_pxl_ready),
    .o_wdata_fifo(wdata_fifo),
    .o_write_en(write_en),
    .i_afull(afull),
    .i_soft_reset(soft_reset),
    .o_interrupt_pb(interrupt_pb)
  );

  //AFIFO SUB MODULE INSTANCE
  asynch_fifo
  #(
    .AFIFO_DEPTH(FIFO_DEPTH),
    .STAGE_NUMBER(STAGE_NUMBER),
    .AFIFO_AFULL_TH(AFIFO_AFULL_TH),
    .AFIFO_DW(AFIFO_DW)
  )
  asynch_fifo_i
  (
    .write_clk(i_f_clk_ao),
    .read_clk(i_txclkhs),
    .write_rst_n(i_reset_fclk_n),
    .read_rst_n(reset_hsclk_n),
    .write_soft_reset(soft_reset),
    .read_soft_reset(soft_reset_hs),
    .write_en(write_en),
    .read_en(read_en),
    .data_in(wdata_fifo),
    .data_out(rdata_fifo),
    .full(),
    .afull(afull),
    .empty(empty)
  );

  //HIGH SPEED TRANSMITTER SUB MODULE INSTANCE
  high_speed_transmitter
  #(
    .HS_DATA_WIDTH(HS_DATA_WIDTH),
    .AFIFO_DW(AFIFO_DW)
  )
  high_speed_transmitter_i
  (
    .i_reset_hsclk_n(reset_hsclk_n),
    .i_hs_dl_reg_dly(hs_dl_reg_dly),
    .i_hs_clk_post(hs_clk_post),
    .i_hs_clk_pre(hs_clk_pre),
    .o_is_idle(is_idle_high_speed_transmitter),
    .i_rdata_fifo(rdata_fifo),
    .o_read_en(read_en),
    .i_empty(empty),
    .i_txclkhs(i_txclkhs),
    .i_txreadyhs(i_txreadyhs),
    .o_txdatahs(o_txdatahs),
    .o_txrequesths(o_txrequesths),
    .o_txrequesths_clk(o_txrequesths_clk),
    .i_soft_reset_hs(soft_reset_hs),
    .o_interrupt_hs(interrupt_hs)
  );

  //SYNCHRONIZATION SUB MODULE INSTANCE
  synchronization synchronization_i
  (
    .i_f_clk_ao(i_f_clk_ao),
    .i_rst_fclk_n(i_reset_fclk_n),
    .o_reset_hsclk_n(reset_hsclk_n),
    .i_txclkhs(i_txclkhs),
    .i_is_idle_packet_builder(is_idle_packet_builder),
    .i_is_idle_high_speed_transmitter(is_idle_high_speed_transmitter),
    .o_hs_clk_pre(hs_clk_pre),
    .o_hs_clk_post(hs_clk_post),
    .o_hs_dl_reg_dly(hs_dl_reg_dly),
    .i_hs_clk_dly(hs_clk_dly),
    .i_write_r(write_r),
    .o_is_idle(is_idle),
    .i_soft_reset(soft_reset),
    .o_soft_reset_hs(soft_reset_hs),
    .i_interrupt_hs(interrupt_hs),
    .o_synch_interrupt_hs(synch_interrupt_hs)
  );

  //APB SLAVE INSTABNCE
  apb_slave apb_slave_i
  (
    .i_f_clk_ao(i_f_clk_ao),
    .i_rst_fclk_n(i_reset_fclk_n),
    .i_paddr(i_paddr),
    .i_psel(i_psel),
    .i_peneble(i_penable),
    .i_pwrite(i_pwrite),
    .i_pwdata(i_pwdata),
    .o_pready(o_pready),
    .o_prdata(o_prdata),
    .o_pslverr(o_pslverr),
    .o_hs_clk_dly(hs_clk_dly),
    .o_pxl_tx_fs_pckt(pxl_tx_fs_pckt),
    .o_pxl_tx_fe_pckt(pxl_tx_fe_pckt),
    .o_pxl_tx_long_pckt(pxl_tx_long_pckt),
    .i_is_idle(is_idle),
    .o_write_r(write_r),
    .o_soft_reset(soft_reset),
    .i_interrupt_pb(interrupt_pb),
    .i_synch_interrupt_hs(synch_interrupt_hs),
    .o_interrupt(o_interrupt)
  );
endmodule
