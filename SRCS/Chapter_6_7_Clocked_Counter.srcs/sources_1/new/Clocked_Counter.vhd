library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Chapter 6 + Chapter 7 combined.
-- The 1 Hz clock from Clock_and_Timing (Ch.7) replaces the manual switch clock
-- of Four_bit_Counter (Ch.6), so the counter steps forward by itself once per second.
--
--   CLK100MHZ -> [Clock_and_Timing] -> slow_clk (1 Hz) -> [Four_bit_Counter] -> output (LD3..LD0)

entity Clocked_Counter is
    Port (
        CLK100MHZ : in std_logic;                        -- 100 MHz board clock
        Rst       : in std_logic;                        -- SW15, active-high reset
        output    : out std_logic_vector(3 downto 0);    -- LD3..LD0, binary count
        clk_led   : out std_logic                        -- LD15, shows the 1 Hz clock
    );
end Clocked_Counter;

architecture Behavioral of Clocked_Counter is

-- Clock and Timing Component Declaration (Chapter 7)
component Clock_and_Timing
    Port (
        source_Clk : in std_logic;
        output     : out std_logic
    );
end component;

-- Four bit Counter Component Declaration (Chapter 6)
component Four_bit_Counter
    Port (
        Rst, Clk : in std_logic;
        output   : out std_logic_vector(3 downto 0)
    );
end component;

-- Intermediate declaration: the wire between the two components
signal slow_clk : std_logic;

begin
    -- Ch.7: divide 100 MHz down to 1 Hz
    CLK_DIV: Clock_and_Timing port map (
                 source_Clk => CLK100MHZ,
                 output     => slow_clk
             );

    -- Ch.6: counter clocked by the 1 Hz signal instead of the manual switch
    COUNTER: Four_bit_Counter port map (
                 Rst    => Rst,
                 Clk    => slow_clk,
                 output => output
             );

    clk_led <= slow_clk;                                 -- blink LED so you can see each tick

end Behavioral;
