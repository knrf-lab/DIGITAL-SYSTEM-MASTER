library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Self-checking testbench for Door_Lock_Top.
-- Run with "run all". The console prints PASS/FAIL for each check
-- and "ALL TESTS PASSED" at the end. Total sim time is about 25 us.
--
-- LED(15) = LOCKED, LED(14) = UNLOCKED, LED(13) = WRONG, LED(3:0) = progress

entity tb_Door_Lock is
end tb_Door_Lock;

architecture Behavioral of tb_Door_Lock is

component Door_Lock_Top
    Generic (
        DEBOUNCE_COUNT : integer
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
end component;

signal CLK100MHZ  : std_logic := '0';
signal CPU_RESETN : std_logic := '0';
signal BTNC, BTNU, BTND : std_logic := '0';
signal SW         : std_logic_vector(3 downto 0) := "0000";
signal LED        : std_logic_vector(15 downto 0);
signal sim_done   : boolean := false;

begin
    -- Short debounce (4 clocks) so the simulation runs fast
    UUT: Door_Lock_Top generic map (DEBOUNCE_COUNT => 4)
                       port map (
                           CLK100MHZ  => CLK100MHZ,
                           CPU_RESETN => CPU_RESETN,
                           BTNC       => BTNC,
                           BTNU       => BTNU,
                           BTND       => BTND,
                           SW         => SW,
                           LED        => LED
                       );

    -- 100 MHz clock (10 ns period), stops when the test is finished
    CLK100MHZ <= not CLK100MHZ after 5 ns when not sim_done else '0';

    STIMULUS: process
        variable errors : integer := 0;

        -- Press and release a button (long enough to pass the debouncer)
        procedure press(signal btn : out std_logic) is
        begin
            btn <= '1';
            wait for 200 ns;
            btn <= '0';
            wait for 200 ns;
        end procedure;

        -- Put a digit on SW[3:0] and press BTNC
        procedure enter_digit(d : in std_logic_vector(3 downto 0)) is
        begin
            SW <= d;
            wait for 50 ns;
            press(BTNC);
        end procedure;

        procedure check(cond : in boolean; msg : in string) is
        begin
            if cond then
                report "PASS: " & msg severity note;
            else
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure;

    begin
        -- Reset
        CPU_RESETN <= '0';
        wait for 100 ns;
        CPU_RESETN <= '1';
        wait for 100 ns;
        check(LED(15) = '1' and LED(14) = '0' and LED(13) = '0', "after reset: LOCKED");

        -- Test 1: correct password 1-2-3-4
        enter_digit("0001");
        check(LED(3 downto 0) = "0001", "T1 progress 1 digit");
        enter_digit("0010");
        check(LED(3 downto 0) = "0011", "T1 progress 2 digits");
        enter_digit("0011");
        check(LED(3 downto 0) = "0111", "T1 progress 3 digits");
        enter_digit("0100");
        check(LED(3 downto 0) = "1111", "T1 progress 4 digits");
        check(LED(15) = '1', "T1 still LOCKED before submit");
        press(BTNC);                                         -- submit
        check(LED(14) = '1' and LED(15) = '0', "T1 correct password -> UNLOCKED");

        -- Test 2: input is blocked while UNLOCKED
        enter_digit("0101");
        check(LED(14) = '1' and LED(3 downto 0) = "0000", "T2 BTNC ignored while UNLOCKED");

        -- Test 3: LOCK button re-locks
        press(BTNU);
        check(LED(15) = '1' and LED(14) = '0', "T3 BTNU -> LOCKED");

        -- Test 4: wrong order 1-2-4-3 -> DENIED
        enter_digit("0001");
        enter_digit("0010");
        enter_digit("0100");
        enter_digit("0011");
        press(BTNC);
        check(LED(13) = '1' and LED(15) = '1' and LED(14) = '0', "T4 wrong password -> DENIED");

        -- Test 5: BTNC clears WRONG and is not counted as a digit
        press(BTNC);
        check(LED(13) = '0' and LED(15) = '1' and LED(3 downto 0) = "0000", "T5 BTNC -> LOCKED, no digit");

        -- Test 6: invalid BCD (10 and 15) is ignored
        enter_digit("1010");
        enter_digit("1111");
        check(LED(3 downto 0) = "0000", "T6 invalid digits ignored");
        enter_digit("0001");
        enter_digit("0010");
        enter_digit("0011");
        enter_digit("0100");
        press(BTNC);
        check(LED(14) = '1', "T6 correct password after invalid digits -> UNLOCKED");
        press(BTNU);

        -- Test 7: BTND clears a half-typed entry
        enter_digit("1001");
        enter_digit("1001");
        check(LED(3 downto 0) = "0011", "T7 two digits entered");
        press(BTND);
        check(LED(3 downto 0) = "0000" and LED(15) = '1', "T7 BTND clears entry");
        enter_digit("0001");
        enter_digit("0010");
        enter_digit("0011");
        enter_digit("0100");
        press(BTNC);
        check(LED(14) = '1', "T7 correct password after clear -> UNLOCKED");

        -- Summary
        if errors = 0 then
            report "ALL TESTS PASSED" severity note;
        else
            report "TESTS FAILED: " & integer'image(errors) & " error(s)" severity error;
        end if;
        sim_done <= true;
        wait;
    end process;

end Behavioral;
