library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity half_adder is
    Port (
        A,B: in STD_LOGIC;
        Cout,Sum: out STD_LOGIC
    );
end half_adder;

architecture Behavioral of half_adder is

begin
Sum <= A xor B;
Cout <= A and B;

end Behavioral;
