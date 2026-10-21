library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Door lock controller (Moore FSM).
--
-- States:
--   LOCKED   : door locked, no digits entered yet
--   ENTERING : some digits entered (digit counter = 1 .. N_DIGITS-1)
--   READY    : all N_DIGITS entered, waiting for submit (BTNC)
--   UNLOCKED : correct password, door open (until LOCK button)
--   DENIED   : wrong password (until next BTNC)
--
-- Inputs btn_confirm / btn_lock / btn_clear must be 1-clock pulses (from Debouncer).
-- digit_in is a BCD digit; values 10..15 (1010..1111) are ignored.

entity Lock_FSM is
    Generic (
        N_DIGITS : integer := 4                          -- number of password digits
    );
    Port (
        clk, rst     : in std_logic;
        btn_confirm  : in std_logic;                     -- BTNC: store digit / submit
        btn_lock     : in std_logic;                     -- BTNU: re-lock the door
        btn_clear    : in std_logic;                     -- BTND: clear current entry
        digit_in     : in std_logic_vector(3 downto 0);  -- SW[3:0], SW0 = LSB
        led_locked   : out std_logic;
        led_unlocked : out std_logic;
        led_wrong    : out std_logic;
        led_progress : out std_logic_vector(N_DIGITS-1 downto 0)
    );
end Lock_FSM;

architecture Behavioral of Lock_FSM is

type state_type is (LOCKED, ENTERING, READY, UNLOCKED, DENIED);
signal state : state_type := LOCKED;

-- Default password 1-2-3-4. First digit entered = leftmost hex digit.
-- NOTE: if N_DIGITS is changed, this constant must have 4*N_DIGITS bits.
constant DEFAULT_PASSWORD : std_logic_vector(4*N_DIGITS-1 downto 0) := x"1234";

signal password    : std_logic_vector(4*N_DIGITS-1 downto 0) := DEFAULT_PASSWORD; -- stored password register
signal entered     : std_logic_vector(4*N_DIGITS-1 downto 0) := (others => '0');  -- digits typed by user
signal count       : integer range 0 to N_DIGITS := 0;                            -- digits entered so far
signal digit_valid : std_logic;

begin
    -- BCD validity check: digit is INVALID (10..15) when D3 = 1 and (D2 = 1 or D1 = 1)
    digit_valid <= not (digit_in(3) and (digit_in(2) or digit_in(1)));

    -- State register + next-state logic
    process(rst, clk)
    begin
        if (rst = '1') then
            state    <= LOCKED;
            entered  <= (others => '0');
            count    <= 0;
            password <= DEFAULT_PASSWORD;
        elsif rising_edge(clk) then
            case state is

                when LOCKED | ENTERING =>
                    if (btn_clear = '1') then
                        entered <= (others => '0');
                        count   <= 0;
                        state   <= LOCKED;
                    elsif (btn_confirm = '1' and digit_valid = '1') then
                        -- shift the new digit in from the right
                        entered <= entered(4*N_DIGITS-5 downto 0) & digit_in;
                        count   <= count + 1;
                        if (count = N_DIGITS - 1) then
                            state <= READY;              -- that was the last digit
                        else
                            state <= ENTERING;
                        end if;
                    end if;                              -- invalid digit: ignored

                when READY =>
                    if (btn_clear = '1') then
                        entered <= (others => '0');
                        count   <= 0;
                        state   <= LOCKED;
                    elsif (btn_confirm = '1') then
                        -- Comparator: entered digits vs stored password
                        if (entered = password) then
                            state <= UNLOCKED;
                        else
                            state <= DENIED;
                        end if;
                        entered <= (others => '0');      -- forget the typed digits
                        count   <= 0;
                    end if;

                when DENIED =>
                    if (btn_confirm = '1' or btn_clear = '1') then
                        state <= LOCKED;                 -- this press is NOT counted as a digit
                    end if;

                when UNLOCKED =>
                    if (btn_lock = '1') then
                        state <= LOCKED;                 -- BTNC and switches are ignored here
                    end if;

            end case;
        end if;
    end process;

    -- Moore outputs (depend only on state and digit counter)
    led_locked   <= '0' when state = UNLOCKED else '1';
    led_unlocked <= '1' when state = UNLOCKED else '0';
    led_wrong    <= '1' when state = DENIED   else '0';

    -- Progress LEDs: LED i is on when more than i digits have been entered
    PROGRESS: for i in 0 to N_DIGITS-1 generate
        led_progress(i) <= '1' when count > i else '0';
    end generate;

end Behavioral;
