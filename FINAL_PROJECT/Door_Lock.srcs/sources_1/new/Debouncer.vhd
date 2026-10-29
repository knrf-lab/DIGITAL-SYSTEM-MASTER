library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Debouncer + rising-edge detector for one push button.
-- Output 'pulse' is high for exactly ONE clock cycle per button press,
-- no matter how long the button is held or how much it bounces.
--
-- Stage 1: 2 flip-flop synchronizer (button is asynchronous to the clock)
-- Stage 2: debounce counter (input must stay stable for DEBOUNCE_COUNT clocks)
-- Stage 3: edge detector (compare stable value with its previous value)

entity Debouncer is
    Generic (
        DEBOUNCE_COUNT : integer := 1000000   -- 1,000,000 x 10 ns = 10 ms at 100 MHz
    );
    Port (
        clk, rst : in std_logic;
        btn_in   : in std_logic;
        pulse    : out std_logic
    );
end Debouncer;

architecture Behavioral of Debouncer is

signal sync_0, sync_1 : std_logic := '0';                 -- synchronizer flip-flops
signal stable         : std_logic := '0';                 -- debounced button level
signal stable_prev    : std_logic := '0';                 -- stable, delayed by 1 clock
signal count          : integer range 0 to DEBOUNCE_COUNT := 0;

begin
    process(rst, clk)
    begin
        if (rst = '1') then
            sync_0      <= '0';
            sync_1      <= '0';
            stable      <= '0';
            stable_prev <= '0';
            count       <= 0;
            pulse       <= '0';
        elsif rising_edge(clk) then
            -- Stage 1: synchronizer
            sync_0 <= btn_in;
            sync_1 <= sync_0;

            -- Stage 2: debounce
            if (sync_1 = stable) then
                count <= 0;                               -- no change, keep counter cleared
            elsif (count = DEBOUNCE_COUNT - 1) then
                stable <= sync_1;                         -- input held long enough, accept it
                count  <= 0;
            else
                count <= count + 1;                       -- input different, keep counting
            end if;

            -- Stage 3: rising-edge detector (0 -> 1 of the debounced level)
            stable_prev <= stable;
            if (stable = '1' and stable_prev = '0') then
                pulse <= '1';
            else
                pulse <= '0';
            end if;
        end if;
    end process;

end Behavioral;
