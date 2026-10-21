library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Half_Adder is
  Port (
      A,B: in std_logic;
      Sum, Cout: out std_logic
  );
end Half_Adder;

architecture Behavioral of Half_Adder is

begin
Sum <= A xor B;
Cout <= A and B;

end Behavioral;
