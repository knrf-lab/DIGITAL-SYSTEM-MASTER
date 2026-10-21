library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity or_gate is
    Port (
        A: in std_logic;
        B: in std_logic;
        output: out std_logic
    );
end or_gate;

architecture Behavioral of or_gate is

begin
output <= A or B;

end Behavioral;
