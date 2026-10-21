library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Top level: connects the board pins (Nexys A7-100T) to the Debouncers and Lock_FSM.
--
--   SW[3:0]   : BCD digit input         LED[3:0] : digit progress
--   BTNC      : confirm digit / submit  LED[13]  : WRONG
--   BTNU      : lock                    LED[14]  : UNLOCKED
--   BTND      : clear entry             LED[15]  : LOCKED
--   CPU_RESETN: global reset (active-low button)

entity Door_Lock_Top is
    Generic (
        DEBOUNCE_COUNT : integer := 1000000              -- 10 ms; testbench sets this small
    );
    Port (
        CLK100MHZ  : in std_logic;
        CPU_RESETN : in std_logic;
        BTNC       : in std_logic;
        BTNU       : in std_logic;
        BTND       : in std_logic;
        SW         : in std_logic_vector(3 downto 0);
        LED        : out std_logic_vector(15 downto 0)
    );
end Door_Lock_Top;

architecture Behavioral of Door_Lock_Top is

-- Debouncer Component Declaration
component Debouncer
    Generic (
        DEBOUNCE_COUNT : integer
    );
    Port (
        clk, rst : in std_logic;
        btn_in   : in std_logic;
        pulse    : out std_logic
    );
end component;

-- Lock FSM Component Declaration
component Lock_FSM
    Generic (
        N_DIGITS : integer
    );
    Port (
        clk, rst     : in std_logic;
        btn_confirm  : in std_logic;
        btn_lock     : in std_logic;
        btn_clear    : in std_logic;
        digit_in     : in std_logic_vector(3 downto 0);
        led_locked   : out std_logic;
        led_unlocked : out std_logic;
        led_wrong    : out std_logic;
        led_progress : out std_logic_vector(N_DIGITS-1 downto 0)
    );
end component;

-- Intermediate declaration
signal rst                            : std_logic;
signal confirm_p, lock_p, clear_p     : std_logic;   -- 1-clock button pulses

begin
    rst <= not CPU_RESETN;                           -- CPU_RESET button is active-low

    -- One debouncer per button
    DB_C: Debouncer generic map (DEBOUNCE_COUNT => DEBOUNCE_COUNT)
                    port map (clk => CLK100MHZ, rst => rst, btn_in => BTNC, pulse => confirm_p);
    DB_U: Debouncer generic map (DEBOUNCE_COUNT => DEBOUNCE_COUNT)
                    port map (clk => CLK100MHZ, rst => rst, btn_in => BTNU, pulse => lock_p);
    DB_D: Debouncer generic map (DEBOUNCE_COUNT => DEBOUNCE_COUNT)
                    port map (clk => CLK100MHZ, rst => rst, btn_in => BTND, pulse => clear_p);

    -- Door lock controller
    FSM: Lock_FSM generic map (N_DIGITS => 4)
                  port map (
                      clk          => CLK100MHZ,
                      rst          => rst,
                      btn_confirm  => confirm_p,
                      btn_lock     => lock_p,
                      btn_clear    => clear_p,
                      digit_in     => SW,
                      led_locked   => LED(15),
                      led_unlocked => LED(14),
                      led_wrong    => LED(13),
                      led_progress => LED(3 downto 0)
                  );

    LED(12 downto 4) <= (others => '0');             -- unused LEDs off

end Behavioral;
