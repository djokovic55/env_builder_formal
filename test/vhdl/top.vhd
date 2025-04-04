library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity top is
  generic (
    DATA_WIDTH : integer := 32;
    ADDR_WIDTH : integer := 32
  );
  port (
        clk : in std_logic;
        reset : in std_logic;

        -- ex_reg top interface 
				pb_irq_i : in std_logic;
				pb_addr_in_i : in std_logic_vector(ADDR_WIDTH-1 downto 0);
				pb_byte_cnt_i : in std_logic_vector(3 downto 0);
				pb_pkt_type_i : in std_logic_vector(3 downto 0);
				pb_ecc_en_i : in std_logic;
				pb_crc_en_i : in std_logic;
				pb_ins_ecc_err_i : in std_logic_vector(1 downto 0);
				pb_ins_crc_err_i : in std_logic;
				pb_ecc_val_i : in std_logic_vector(3 downto 0);
				pb_crc_val_i: in std_logic_vector(7 downto 0);
				pb_sop_val_i: in std_logic_vector(2 downto 0);
				pb_data_sel_i: in std_logic_vector(3 downto 0);
				pb_addr_out_i: in std_logic_vector(DATA_WIDTH-1 downto 0);

				pp_irq_i : in std_logic;
				pp_addr_hdr_i : in std_logic_vector(ADDR_WIDTH-1 downto 0);
				pp_ignore_ecc_err_i : in std_logic;

        -- inmem port B top interface, used for memory configuration
        inmem_en_b_i	: in std_logic;
        inmem_data_b_i	: in std_logic_vector(31 downto 0);
        inmem_addr_b_i	: in std_logic_vector(13 downto 0);
        inmem_we_b_i	: in std_logic_vector(3 downto 0);
        inmem_data_b_o	: out std_logic_vector(31 downto 0);

        -- outmem port B top interface, memory read only
        outmem_en_b_i	: in std_logic;
        outmem_data_b_i	: in std_logic_vector(31 downto 0);
        outmem_addr_b_i	: in std_logic_vector(13 downto 0);
        outmem_we_b_i	: in std_logic_vector(3 downto 0);
        outmem_data_b_o	: out std_logic_vector(31 downto 0);

				-- controller top status
				cont_busy_top : out std_logic;
				
        -- regs_top interface
        pb0_start_top : out std_logic;
        pb0_busy_top : out std_logic;
        pb0_irq_top : out std_logic;
        pb0_addr_in_top : out std_logic_vector(ADDR_WIDTH-1 downto 0);
        pb0_byte_cnt_top : out std_logic_vector(3 downto 0);
        pb0_pkt_type_top : out std_logic_vector(3 downto 0);
        pb0_ecc_en_top : out std_logic;
        pb0_crc_en_top : out std_logic;
        pb0_ins_ecc_err_top : out std_logic_vector(1 downto 0);
        pb0_ins_crc_err_top : out std_logic;
        pb0_ecc_val_top : out std_logic_vector(3 downto 0);
        pb0_crc_val_top: out std_logic_vector(7 downto 0);
        pb0_sop_val_top: out std_logic_vector(2 downto 0);
        pb0_data_sel_top: out std_logic_vector(3 downto 0);
        pb0_addr_out_top: out std_logic_vector(31 downto 0);

        -- [x] if with builder1
        pb1_start_top : out std_logic;
        pb1_busy_top : out std_logic;
        pb1_irq_top : out std_logic;
        pb1_addr_in_top : out std_logic_vector(ADDR_WIDTH-1 downto 0);
        pb1_byte_cnt_top : out std_logic_vector(3 downto 0);
        pb1_pkt_type_top : out std_logic_vector(3 downto 0);
        pb1_ecc_en_top : out std_logic;
        pb1_crc_en_top : out std_logic;
        pb1_ins_ecc_err_top : out std_logic_vector(1 downto 0);
        pb1_ins_crc_err_top : out std_logic;
        pb1_ecc_val_top : out std_logic_vector(3 downto 0);
        pb1_crc_val_top: out std_logic_vector(7 downto 0);
        pb1_sop_val_top: out std_logic_vector(2 downto 0);
        pb1_data_sel_top: out std_logic_vector(3 downto 0);
        pb1_addr_out_top: out std_logic_vector(31 downto 0);

        -- [x] if with parser
        pp_start_top : out std_logic;
        pp_busy_top : out std_logic;
        pp_irq_top : out std_logic;
        pp_addr_hdr_top : out std_logic_vector(ADDR_WIDTH-1 downto 0);
        pp_ignore_ecc_err_top : out std_logic;
        pp_pkt_ecc_corr_top : out std_logic;
        pp_pkt_ecc_uncorr_top : out std_logic;
        pp_pkt_crc_err_top : out std_logic;
        pp_pkt_byte_cnt_top : out std_logic_vector(3 downto 0);
        pp_pkt_type_top : out std_logic_vector(3 downto 0)
  );
end entity;
-- some test

architecture rtl of top is

  --------------------------------------------------------------------------------
  -- subsystem
  --------------------------------------------------------------------------------

component top_subsystem is
  generic (
    DATA_WIDTH : integer := 32;
    ADDR_WIDTH : integer := 32
  );
  port (
				cont_busy_top : out std_logic;
        clk : in std_logic;
        reset : in std_logic;

        -- ex_reg top interface 
				pb_irq_i : in std_logic;
				pb_addr_in_i : in std_logic_vector(ADDR_WIDTH-1 downto 0);
				pb_byte_cnt_i : in std_logic_vector(3 downto 0);
				pb_pkt_type_i : in std_logic_vector(3 downto 0);
				pb_ecc_en_i : in std_logic;
				pb_crc_en_i : in std_logic;
				pb_ins_ecc_err_i : in std_logic_vector(1 downto 0);
				pb_ins_crc_err_i : in std_logic;
				pb_ecc_val_i : in std_logic_vector(3 downto 0);
				pb_crc_val_i: in std_logic_vector(7 downto 0);
				pb_sop_val_i: in std_logic_vector(2 downto 0);
				pb_data_sel_i: in std_logic_vector(3 downto 0);
				pb_addr_out_i: in std_logic_vector(DATA_WIDTH-1 downto 0);

				pp_irq_i : in std_logic;
				pp_addr_hdr_i : in std_logic_vector(ADDR_WIDTH-1 downto 0);
				pp_ignore_ecc_err_i : in std_logic;

        -- Inemem interface - same names as in interconnect
        -- ADDRESS WRITE CHANNEL
        m_axi_int_awaddr_inmem: out std_logic_vector(ADDR_WIDTH-1 downto 0);
        m_axi_int_awlen_inmem: out std_logic_vector(7 downto 0);
        m_axi_int_awsize_inmem: out std_logic_vector(2 downto 0);
        m_axi_int_awburst_inmem: out std_logic_vector(1 downto 0);

        m_axi_int_awvalid_inmem: out std_logic;
        m_axi_int_awready_inmem: in std_logic;

        -- WRITE DATA CHANNEL
        m_axi_int_wdata_inmem: out std_logic_vector(DATA_WIDTH-1 downto 0);
        m_axi_int_wstrb_inmem: out std_logic_vector(DATA_WIDTH/8-1 downto 0);
        m_axi_int_wlast_inmem: out std_logic;

        m_axi_int_wvalid_inmem: out std_logic;
        m_axi_int_wready_inmem: in std_logic;

        -- WRITE RESPONSE CHANNEL
        m_axi_int_bresp_inmem: in std_logic_vector(1 downto 0);
        m_axi_int_bvalid_inmem: in std_logic;
        m_axi_int_bready_inmem: out std_logic;

        -- READ ADDRESS CHANNEL
        m_axi_int_araddr_inmem: out std_logic_vector(ADDR_WIDTH-1 downto 0);
        m_axi_int_arlen_inmem: out std_logic_vector(7 downto 0);
        m_axi_int_arsize_inmem: out std_logic_vector(2 downto 0);
        m_axi_int_arburst_inmem: out std_logic_vector(1 downto 0);

        m_axi_int_arvalid_inmem: out std_logic;
        m_axi_int_arready_inmem: in std_logic;

        -- READ DATA CHANNEL
        m_axi_int_rdata_inmem: in std_logic_vector(DATA_WIDTH-1 downto 0);
        m_axi_int_rresp_inmem: in std_logic_vector(1 downto 0);
        m_axi_int_rlast_inmem: in std_logic;

        m_axi_int_rvalid_inmem: in std_logic;
        m_axi_int_rready_inmem: out std_logic;
        --------------------------------------------------------------------------------

        -- ADDRESS WRITE CHANNEL
        m_axi_int_awaddr_outmem: out std_logic_vector(ADDR_WIDTH-1 downto 0);
        m_axi_int_awlen_outmem: out std_logic_vector(7 downto 0);
        m_axi_int_awsize_outmem: out std_logic_vector(2 downto 0);
        m_axi_int_awburst_outmem: out std_logic_vector(1 downto 0);

        m_axi_int_awvalid_outmem: out std_logic;
        m_axi_int_awready_outmem: in std_logic;

            -- WRITE DATA CHANNEL
        m_axi_int_wdata_outmem: out std_logic_vector(DATA_WIDTH-1 downto 0);
        m_axi_int_wstrb_outmem: out std_logic_vector(DATA_WIDTH/8-1 downto 0);
        m_axi_int_wlast_outmem: out std_logic;

        m_axi_int_wvalid_outmem: out std_logic;
        m_axi_int_wready_outmem: in std_logic;

            -- WRITE RESPONSE CHANNEL
        m_axi_int_bresp_outmem: in std_logic_vector(1 downto 0);
        m_axi_int_bvalid_outmem: in std_logic;
        m_axi_int_bready_outmem: out std_logic;

            -- READ ADDRESS CHANNEL
        m_axi_int_araddr_outmem: out std_logic_vector(ADDR_WIDTH-1 downto 0);
        m_axi_int_arlen_outmem: out std_logic_vector(7 downto 0);
        m_axi_int_arsize_outmem: out std_logic_vector(2 downto 0);
        m_axi_int_arburst_outmem: out std_logic_vector(1 downto 0);

        m_axi_int_arvalid_outmem: out std_logic;
        m_axi_int_arready_outmem: in std_logic;

            -- READ DATA CHANNEL
        m_axi_int_rdata_outmem: in std_logic_vector(DATA_WIDTH-1 downto 0);
        m_axi_int_rresp_outmem: in std_logic_vector(1 downto 0);
        m_axi_int_rlast_outmem: in std_logic;

        m_axi_int_rvalid_outmem: in std_logic;
        m_axi_int_rready_outmem: out std_logic;
        --------------------------------------------------------------------------------

        -- regs top interface
        pb0_start_top : out std_logic;
        pb0_busy_top : out std_logic;
        pb0_irq_top : out std_logic;
        pb0_addr_in_top : out std_logic_vector(ADDR_WIDTH-1 downto 0);
        pb0_byte_cnt_top : out std_logic_vector(3 downto 0);
        pb0_pkt_type_top : out std_logic_vector(3 downto 0);
        pb0_ecc_en_top : out std_logic;
        pb0_crc_en_top : out std_logic;
        pb0_ins_ecc_err_top : out std_logic_vector(1 downto 0);
        pb0_ins_crc_err_top : out std_logic;
        pb0_ecc_val_top : out std_logic_vector(3 downto 0);
        pb0_crc_val_top: out std_logic_vector(7 downto 0);
        pb0_sop_val_top: out std_logic_vector(2 downto 0);
        pb0_data_sel_top: out std_logic_vector(3 downto 0);
        pb0_addr_out_top: out std_logic_vector(31 downto 0);

        -- [x] interface with builder1
        pb1_start_top : out std_logic;
        pb1_busy_top : out std_logic;
        pb1_irq_top : out std_logic;
        pb1_addr_in_top : out std_logic_vector(ADDR_WIDTH-1 downto 0);
        pb1_byte_cnt_top : out std_logic_vector(3 downto 0);
        pb1_pkt_type_top : out std_logic_vector(3 downto 0);
        pb1_ecc_en_top : out std_logic;
        pb1_crc_en_top : out std_logic;
        pb1_ins_ecc_err_top : out std_logic_vector(1 downto 0);
        pb1_ins_crc_err_top : out std_logic;
        pb1_ecc_val_top : out std_logic_vector(3 downto 0);
        pb1_crc_val_top: out std_logic_vector(7 downto 0);
        pb1_sop_val_top: out std_logic_vector(2 downto 0);
        pb1_data_sel_top: out std_logic_vector(3 downto 0);
        pb1_addr_out_top: out std_logic_vector(31 downto 0);
        -- [x] interface with parser

        pp_start_top : out std_logic;
        pp_busy_top : out std_logic;
        pp_irq_top : out std_logic;
        pp_addr_hdr_top : out std_logic_vector(ADDR_WIDTH-1 downto 0);
        pp_ignore_ecc_err_top : out std_logic;
        pp_pkt_ecc_corr_top : out std_logic;
        pp_pkt_ecc_uncorr_top : out std_logic;
        pp_pkt_crc_err_top : out std_logic;
        pp_pkt_byte_cnt_top : out std_logic_vector(3 downto 0);
        pp_pkt_type_top : out std_logic_vector(3 downto 0)
  );
end component;

  --------------------------------------------------------------------------------
  -- Memory
  --------------------------------------------------------------------------------
  component data_memory is
  generic (

		C_S_AXI_DATA_WIDTH	: integer	:= 32;
		C_S_AXI_ADDR_WIDTH	: integer	:= 32
    
  );
  port (

		-- Global Clock Signal
		S_AXI_ACLK	: in std_logic;
		-- Global Reset Signal. This Signal is Active LOW
		S_AXI_ARESETN	: in std_logic;

		--------------------------------------------------------------------------------
		-- Memory B port - top level use
		--------------------------------------------------------------------------------
		en_b_i	: in std_logic;
		data_b_i	: in std_logic_vector(31 downto 0);
		addr_b_i	: in std_logic_vector(13 downto 0);
		we_b_i	: in std_logic_vector(3 downto 0);
		data_b_o	: out std_logic_vector(31 downto 0);

		--------------------------------------------------------------------------------
		-- SLAVE INTERFACE WRITE ADDRESS
		--------------------------------------------------------------------------------
		-- Write address
		S_AXI_AWADDR	: in std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
		-- Burst length. The burst length gives the exact number of transfers in a burst
		S_AXI_AWLEN	: in std_logic_vector(7 downto 0);
		-- Burst size. This signal indicates the size of each transfer in the burst
		S_AXI_AWSIZE	: in std_logic_vector(2 downto 0);
		-- Burst type. The burst type and the size information, 
    -- determine how the address for each transfer within the burst is calculated.
		S_AXI_AWBURST	: in std_logic_vector(1 downto 0);
		-- Write address valid. This signal indicates that
    -- the channel is signaling valid write address and
    -- control information.
		S_AXI_AWVALID	: in std_logic;
		-- Write address ready. This signal indicates that
    -- the slave is ready to accept an address and associated
    -- control signals.
		S_AXI_AWREADY	: out std_logic;

		--------------------------------------------------------------------------------
		-- SLAVE INTERFACE WRITE DATA
		--------------------------------------------------------------------------------
		-- Write Data
		S_AXI_WDATA	: in std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		-- Write strobes. This signal indicates which byte
    -- lanes hold valid data. There is one write strobe
    -- bit for each eight bits of the write data bus.
		S_AXI_WSTRB	: in std_logic_vector((C_S_AXI_DATA_WIDTH/8)-1 downto 0);
		-- Write last. This signal indicates the last transfer
    -- in a write burst.
		S_AXI_WLAST	: in std_logic;
		-- Write valid. This signal indicates that valid write
    -- data and strobes are available.
		S_AXI_WVALID	: in std_logic;
		-- Write ready. This signal indicates that the slave
    -- can accept the write data.
		S_AXI_WREADY	: out std_logic;

		--------------------------------------------------------------------------------
		-- SLAVE INTERFACE WRITE RESPONSE.
		--------------------------------------------------------------------------------
		-- Write response. This signal indicates the status
    -- of the write transaction.
		S_AXI_BRESP	: out std_logic_vector(1 downto 0);
		-- Write response valid. This signal indicates that the
    -- channel is signaling a valid write response.
		S_AXI_BVALID	: out std_logic;
		-- Response ready. This signal indicates that the master
    -- can accept a write response.
		S_AXI_BREADY	: in std_logic;

		--------------------------------------------------------------------------------
		-- SLAVE INTERFACE READ ADDRESS.
		--------------------------------------------------------------------------------
		-- Read address. This signal indicates the initial
    -- address of a read burst transaction.
		S_AXI_ARADDR	: in std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
		-- Burst length. The burst length gives the exact number of transfers in a burst
		S_AXI_ARLEN	: in std_logic_vector(7 downto 0);
		-- Burst size. This signal indicates the size of each transfer in the burst
		S_AXI_ARSIZE	: in std_logic_vector(2 downto 0);
		-- Burst type. The burst type and the size information, 
    -- determine how the address for each transfer within the burst is calculated.
		S_AXI_ARBURST	: in std_logic_vector(1 downto 0);
		-- Write address valid. This signal indicates that
    -- the channel is signaling valid read address and
    -- control information.
		S_AXI_ARVALID	: in std_logic;
		-- Read address ready. This signal indicates that
    -- the slave is ready to accept an address and associated
    -- control signals.
		S_AXI_ARREADY	: out std_logic;

		--------------------------------------------------------------------------------
		-- MASTER READ DATA
		--------------------------------------------------------------------------------
		-- Read Data
		S_AXI_RDATA	: out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
		-- Read response. This signal indicates the status of
    -- the read transfer.
		S_AXI_RRESP	: out std_logic_vector(1 downto 0);
		-- Read last. This signal indicates the last transfer
    -- in a read burst.
		S_AXI_RLAST	: out std_logic;
		-- Read valid. This signal indicates that the channel
    -- is signaling the required read data.
		S_AXI_RVALID	: out std_logic;
		-- Read ready. This signal indicates that the master can
    -- accept the read data and response information.
		S_AXI_RREADY	: in std_logic
  );
  end component;



  --------------------------------------------------------------------------------
  -- SLAVES
  --------------------------------------------------------------------------------
  signal m_axi_int_awaddr_inmem           : std_logic_vector(ADDR_WIDTH-1 downto 0);                                                  
  signal m_axi_int_awlen_inmem            : std_logic_vector(7 downto 0);                                                 
  signal m_axi_int_awsize_inmem           : std_logic_vector(2 downto 0);                                                  
  signal m_axi_int_awburst_inmem          : std_logic_vector(1 downto 0);                                                   
  signal m_axi_int_awvalid_inmem          : std_logic;                                                   
  signal m_axi_int_awready_inmem          : std_logic;                                                   
  signal m_axi_int_wdata_inmem            : std_logic_vector(DATA_WIDTH-1 downto 0);                                                 
  signal m_axi_int_wstrb_inmem            : std_logic_vector(DATA_WIDTH/8-1 downto 0);                                                 
  signal m_axi_int_wlast_inmem            : std_logic;                                                 
  signal m_axi_int_wvalid_inmem           : std_logic;                                                  
  signal m_axi_int_wready_inmem           : std_logic;                                                  
  signal m_axi_int_bresp_inmem            : std_logic_vector(1 downto 0);                                                 
  signal m_axi_int_bvalid_inmem           : std_logic;                                                  
  signal m_axi_int_bready_inmem           : std_logic;                                                  
  signal m_axi_int_araddr_inmem           : std_logic_vector(ADDR_WIDTH-1 downto 0);                                                  
  signal m_axi_int_arlen_inmem            : std_logic_vector(7 downto 0);                                                 
  signal m_axi_int_arsize_inmem           : std_logic_vector(2 downto 0);                                                  
  signal m_axi_int_arburst_inmem          : std_logic_vector(1 downto 0);                                                   
  signal m_axi_int_arvalid_inmem          : std_logic;                                                   
  signal m_axi_int_arready_inmem          : std_logic;                                                   
  signal m_axi_int_rdata_inmem            : std_logic_vector(DATA_WIDTH-1 downto 0);                                                 
  signal m_axi_int_rresp_inmem            : std_logic_vector(1 downto 0);                                                 
  signal m_axi_int_rlast_inmem            : std_logic;                                                 
  signal m_axi_int_rvalid_inmem           : std_logic;                                                  
  signal m_axi_int_rready_inmem           : std_logic;                                                  
  --------------------------------------------------------------------------------

  signal m_axi_int_awaddr_outmem : std_logic_vector(ADDR_WIDTH-1 downto 0);
  signal m_axi_int_awlen_outmem : std_logic_vector(7 downto 0);
  signal m_axi_int_awsize_outmem : std_logic_vector(2 downto 0);
  signal m_axi_int_awburst_outmem : std_logic_vector(1 downto 0);
  signal m_axi_int_awvalid_outmem : std_logic;
  signal m_axi_int_awready_outmem : std_logic;
  signal m_axi_int_wdata_outmem : std_logic_vector(DATA_WIDTH-1 downto 0);
  signal m_axi_int_wstrb_outmem : std_logic_vector(DATA_WIDTH/8-1 downto 0);
  signal m_axi_int_wlast_outmem : std_logic;
  signal m_axi_int_wvalid_outmem : std_logic;
  signal m_axi_int_wready_outmem : std_logic;
  signal m_axi_int_bresp_outmem : std_logic_vector(1 downto 0);
  signal m_axi_int_bvalid_outmem : std_logic;
  signal m_axi_int_bready_outmem : std_logic;
  signal m_axi_int_araddr_outmem : std_logic_vector(ADDR_WIDTH-1 downto 0);
  signal m_axi_int_arlen_outmem : std_logic_vector(7 downto 0);
  signal m_axi_int_arsize_outmem : std_logic_vector(2 downto 0);
  signal m_axi_int_arburst_outmem : std_logic_vector(1 downto 0);
  signal m_axi_int_arvalid_outmem : std_logic;
  signal m_axi_int_arready_outmem : std_logic;
  signal m_axi_int_rdata_outmem : std_logic_vector(DATA_WIDTH-1 downto 0);
  signal m_axi_int_rresp_outmem : std_logic_vector(1 downto 0);
  signal m_axi_int_rlast_outmem : std_logic;
  signal m_axi_int_rvalid_outmem : std_logic;
  signal m_axi_int_rready_outmem : std_logic;
  --------------------------------------------------------------------------------

begin
	

  inmem: data_memory
  generic map(
    C_S_AXI_DATA_WIDTH => DATA_WIDTH,
    C_S_AXI_ADDR_WIDTH => ADDR_WIDTH
  ) 

  port map(
		S_AXI_ACLK => clk,
		S_AXI_ARESETN => reset,

    en_b_i => inmem_en_b_i,
    data_b_i => inmem_data_b_i,
    addr_b_i => inmem_addr_b_i(13 downto 0),
    we_b_i => inmem_we_b_i,
    data_b_o  => inmem_data_b_o,

		S_AXI_AWADDR => m_axi_int_awaddr_inmem,
		S_AXI_AWLEN => m_axi_int_awlen_inmem,
		S_AXI_AWSIZE => m_axi_int_awsize_inmem,
		S_AXI_AWBURST => m_axi_int_awburst_inmem,
		S_AXI_AWVALID => m_axi_int_awvalid_inmem,
		S_AXI_AWREADY => m_axi_int_awready_inmem,
		S_AXI_WDATA => m_axi_int_wdata_inmem,
		S_AXI_WSTRB => m_axi_int_wstrb_inmem,
		S_AXI_WLAST => m_axi_int_wlast_inmem,
		S_AXI_WVALID => m_axi_int_wvalid_inmem,
		S_AXI_WREADY => m_axi_int_wready_inmem,
		S_AXI_BRESP => m_axi_int_bresp_inmem,
		S_AXI_BVALID => m_axi_int_bvalid_inmem,
		S_AXI_BREADY => m_axi_int_bready_inmem,
		S_AXI_ARADDR => m_axi_int_araddr_inmem,
		S_AXI_ARLEN => m_axi_int_arlen_inmem,
		S_AXI_ARSIZE => m_axi_int_arsize_inmem,
		S_AXI_ARBURST => m_axi_int_arburst_inmem,
		S_AXI_ARVALID => m_axi_int_arvalid_inmem,
		S_AXI_ARREADY => m_axi_int_arready_inmem,
		S_AXI_RDATA => m_axi_int_rdata_inmem,
		S_AXI_RRESP => m_axi_int_rresp_inmem,
		S_AXI_RLAST => m_axi_int_rlast_inmem,
		S_AXI_RVALID => m_axi_int_rvalid_inmem,
		S_AXI_RREADY => m_axi_int_rready_inmem

  );

  outmem: data_memory
  generic map(
    C_S_AXI_DATA_WIDTH => DATA_WIDTH,
    C_S_AXI_ADDR_WIDTH => ADDR_WIDTH
  ) 

  port map(
		S_AXI_ACLK => clk,
		S_AXI_ARESETN => reset,

    en_b_i => outmem_en_b_i,
    data_b_i => outmem_data_b_i,
    addr_b_i => outmem_addr_b_i(13 downto 0),
    we_b_i => outmem_we_b_i,
    data_b_o  => outmem_data_b_o,

		S_AXI_AWADDR => m_axi_int_awaddr_outmem,
		S_AXI_AWLEN => m_axi_int_awlen_outmem,
		S_AXI_AWSIZE => m_axi_int_awsize_outmem,
		S_AXI_AWBURST => m_axi_int_awburst_outmem,
		S_AXI_AWVALID => m_axi_int_awvalid_outmem,
		S_AXI_AWREADY => m_axi_int_awready_outmem,
		S_AXI_WDATA => m_axi_int_wdata_outmem,
		S_AXI_WSTRB => m_axi_int_wstrb_outmem,
		S_AXI_WLAST => m_axi_int_wlast_outmem,
		S_AXI_WVALID => m_axi_int_wvalid_outmem,
		S_AXI_WREADY => m_axi_int_wready_outmem,
		S_AXI_BRESP => m_axi_int_bresp_outmem,
		S_AXI_BVALID => m_axi_int_bvalid_outmem,
		S_AXI_BREADY => m_axi_int_bready_outmem,
		S_AXI_ARADDR => m_axi_int_araddr_outmem,
		S_AXI_ARLEN => m_axi_int_arlen_outmem,
		S_AXI_ARSIZE => m_axi_int_arsize_outmem,
		S_AXI_ARBURST => m_axi_int_arburst_outmem,
		S_AXI_ARVALID => m_axi_int_arvalid_outmem,
		S_AXI_ARREADY => m_axi_int_arready_outmem,
		S_AXI_RDATA => m_axi_int_rdata_outmem,
		S_AXI_RRESP => m_axi_int_rresp_outmem,
		S_AXI_RLAST => m_axi_int_rlast_outmem,
		S_AXI_RVALID => m_axi_int_rvalid_outmem,
		S_AXI_RREADY => m_axi_int_rready_outmem
  );

 subsys: top_subsystem 
  generic map(
    DATA_WIDTH                    => DATA_WIDTH,                                
    ADDR_WIDTH                    => ADDR_WIDTH                                
  )
  port map(
    clk                           => clk,                        
    reset                         => reset,                          

		cont_busy_top 								=> cont_busy_top,
        -- ex_reg top interface 
    pb_irq_i                      => pb_irq_i ,                             
    pb_addr_in_i                  => pb_addr_in_i ,                                 
    pb_byte_cnt_i                 => pb_byte_cnt_i ,                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
    pb_pkt_type_i                 => pb_pkt_type_i ,                                  
    pb_ecc_en_i                   => pb_ecc_en_i ,                                
    pb_crc_en_i                   => pb_crc_en_i ,                                
    pb_ins_ecc_err_i              => pb_ins_ecc_err_i ,                                     
    pb_ins_crc_err_i              => pb_ins_crc_err_i ,                                     
    pb_ecc_val_i                  => pb_ecc_val_i ,                                 
    pb_crc_val_i                  => pb_crc_val_i,                                 
    pb_sop_val_i                  => pb_sop_val_i,                                 
    pb_data_sel_i                 => pb_data_sel_i,                                  
    pb_addr_out_i                 => pb_addr_out_i,                                  
    pp_irq_i                      => pp_irq_i ,                             
    pp_addr_hdr_i                 => pp_addr_hdr_i ,                                  
    pp_ignore_ecc_err_i           => pp_ignore_ecc_err_i ,                                        

        -- Inemem interface - same names as in interconnect
    m_axi_int_awaddr_inmem        => m_axi_int_awaddr_inmem,                                           
    m_axi_int_awlen_inmem         => m_axi_int_awlen_inmem,                                          
    m_axi_int_awsize_inmem        => m_axi_int_awsize_inmem,                                           
    m_axi_int_awburst_inmem       => m_axi_int_awburst_inmem,                                            
    m_axi_int_awvalid_inmem       => m_axi_int_awvalid_inmem,                                            
    m_axi_int_awready_inmem       => m_axi_int_awready_inmem,                                            
    m_axi_int_wdata_inmem         => m_axi_int_wdata_inmem,                                          
    m_axi_int_wstrb_inmem         => m_axi_int_wstrb_inmem,                                          
    m_axi_int_wlast_inmem         => m_axi_int_wlast_inmem,                                          
    m_axi_int_wvalid_inmem        => m_axi_int_wvalid_inmem,                                           
    m_axi_int_wready_inmem        => m_axi_int_wready_inmem,                                           
    m_axi_int_bresp_inmem         => m_axi_int_bresp_inmem,                                          
    m_axi_int_bvalid_inmem        => m_axi_int_bvalid_inmem,                                           
    m_axi_int_bready_inmem        => m_axi_int_bready_inmem,                                           
    m_axi_int_araddr_inmem        => m_axi_int_araddr_inmem,                                           
    m_axi_int_arlen_inmem         => m_axi_int_arlen_inmem,                                          
    m_axi_int_arsize_inmem        => m_axi_int_arsize_inmem,                                           
    m_axi_int_arburst_inmem       => m_axi_int_arburst_inmem,                                            
    m_axi_int_arvalid_inmem       => m_axi_int_arvalid_inmem,                                            
    m_axi_int_arready_inmem       => m_axi_int_arready_inmem,                                            
    m_axi_int_rdata_inmem         => m_axi_int_rdata_inmem,                                          
    m_axi_int_rresp_inmem         => m_axi_int_rresp_inmem,                                          
    m_axi_int_rlast_inmem         => m_axi_int_rlast_inmem,                                          
    m_axi_int_rvalid_inmem        => m_axi_int_rvalid_inmem,                                           
    m_axi_int_rready_inmem        => m_axi_int_rready_inmem,                                           
    m_axi_int_awaddr_outmem       => m_axi_int_awaddr_outmem,                                            
    m_axi_int_awlen_outmem        => m_axi_int_awlen_outmem,                                           
    m_axi_int_awsize_outmem       => m_axi_int_awsize_outmem,                                            
    m_axi_int_awburst_outmem      => m_axi_int_awburst_outmem,                                             
    m_axi_int_awvalid_outmem      => m_axi_int_awvalid_outmem,                                             
    m_axi_int_awready_outmem      => m_axi_int_awready_outmem,                                             
    m_axi_int_wdata_outmem        => m_axi_int_wdata_outmem,                                           
    m_axi_int_wstrb_outmem        => m_axi_int_wstrb_outmem,                                           
    m_axi_int_wlast_outmem        => m_axi_int_wlast_outmem,                                           
    m_axi_int_wvalid_outmem       => m_axi_int_wvalid_outmem,                                            
    m_axi_int_wready_outmem       => m_axi_int_wready_outmem,                                            
    m_axi_int_bresp_outmem        => m_axi_int_bresp_outmem,                                           
    m_axi_int_bvalid_outmem       => m_axi_int_bvalid_outmem,                                            
    m_axi_int_bready_outmem       => m_axi_int_bready_outmem,                                            
    m_axi_int_araddr_outmem       => m_axi_int_araddr_outmem,                                            
    m_axi_int_arlen_outmem        => m_axi_int_arlen_outmem,                                           
    m_axi_int_arsize_outmem       => m_axi_int_arsize_outmem,                                            
    m_axi_int_arburst_outmem      => m_axi_int_arburst_outmem,                                             
    m_axi_int_arvalid_outmem      => m_axi_int_arvalid_outmem,                                             
    m_axi_int_arready_outmem      => m_axi_int_arready_outmem,                                             
    m_axi_int_rdata_outmem        => m_axi_int_rdata_outmem,                                           
    m_axi_int_rresp_outmem        => m_axi_int_rresp_outmem,                                           
    m_axi_int_rlast_outmem        => m_axi_int_rlast_outmem,                                           
    m_axi_int_rvalid_outmem       => m_axi_int_rvalid_outmem,                                            
    m_axi_int_rready_outmem       => m_axi_int_rready_outmem,                                            

        -- regs top interface
    pb0_start_top                 => pb0_start_top ,                                  
    pb0_busy_top                  => pb0_busy_top ,                                 
    pb0_irq_top                   => pb0_irq_top ,                                
    pb0_addr_in_top               => pb0_addr_in_top ,                                    
    pb0_byte_cnt_top              => pb0_byte_cnt_top ,                                     
    pb0_pkt_type_top              => pb0_pkt_type_top ,                                     
    pb0_ecc_en_top                => pb0_ecc_en_top ,                                   
    pb0_crc_en_top                => pb0_crc_en_top ,                                   
    pb0_ins_ecc_err_top           => pb0_ins_ecc_err_top ,                                        
    pb0_ins_crc_err_top           => pb0_ins_crc_err_top ,                                        
    pb0_ecc_val_top               => pb0_ecc_val_top ,                                    
    pb0_crc_val_top               => pb0_crc_val_top,                                    
    pb0_sop_val_top               => pb0_sop_val_top,                                    
    pb0_data_sel_top              => pb0_data_sel_top,                                     
    pb0_addr_out_top              => pb0_addr_out_top,                                     
    pb1_start_top                 => pb1_start_top ,                                  
    pb1_busy_top                  => pb1_busy_top ,                                 
    pb1_irq_top                   => pb1_irq_top ,                                
    pb1_addr_in_top               => pb1_addr_in_top ,                                    
    pb1_byte_cnt_top              => pb1_byte_cnt_top ,                                     
    pb1_pkt_type_top              => pb1_pkt_type_top ,                                     
    pb1_ecc_en_top                => pb1_ecc_en_top ,                                   
    pb1_crc_en_top                => pb1_crc_en_top ,                                   
    pb1_ins_ecc_err_top           => pb1_ins_ecc_err_top ,                                        
    pb1_ins_crc_err_top           => pb1_ins_crc_err_top ,                                        
    pb1_ecc_val_top               => pb1_ecc_val_top ,                                    
    pb1_crc_val_top               => pb1_crc_val_top,                                    
    pb1_sop_val_top               => pb1_sop_val_top,                                    
    pb1_data_sel_top              => pb1_data_sel_top,                                     
    pb1_addr_out_top              => pb1_addr_out_top,                                     
    pp_start_top                  => pp_start_top ,                                 
    pp_busy_top                   => pp_busy_top ,                                
    pp_irq_top                    => pp_irq_top ,                               
    pp_addr_hdr_top               => pp_addr_hdr_top ,                                    
    pp_ignore_ecc_err_top         => pp_ignore_ecc_err_top ,                                          
    pp_pkt_ecc_corr_top           => pp_pkt_ecc_corr_top ,                                        
    pp_pkt_ecc_uncorr_top         => pp_pkt_ecc_uncorr_top ,                                          
    pp_pkt_crc_err_top            => pp_pkt_crc_err_top ,                                       
    pp_pkt_byte_cnt_top           => pp_pkt_byte_cnt_top ,                                        
    pp_pkt_type_top               => pp_pkt_type_top                                    
  );
end architecture;
