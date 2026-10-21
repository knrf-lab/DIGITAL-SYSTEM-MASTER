library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Two_Bit_Multiplier is
  Port (
      A1,A0,B1,B0: in std_logic;
      output: out std_logic_vector (3 downto 0)
  );
end Two_Bit_Multiplier;

architecture Behavioral of Two_Bit_Multiplier is
----------half adder component----------
component Half_Adder is
    port(
        A,B: in std_logic ;
        Sum,Cout: out std_logic 
    );
end component ;

signal S1, S2, S3, S4: std_logic;

begin
output(0) <= A0 and B0;
S1 <= A0 and B1;
S2 <= A1 and B0;
S4 <= A1 and B1;

HA1: Half_Adder port map (S1, S2, output(1), S3);
HA2: Half_Adder port map (S3, S4, output(2), output(3));

end Behavioral;
