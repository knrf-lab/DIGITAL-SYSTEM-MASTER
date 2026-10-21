library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Intro_to_Fpga is
  Port (
      Input1: in std_logic;
      Input2: in std_logic;
      Output1: out std_logic;
      Output2: out std_logic;
      Output3: out std_logic
  );
end Intro_to_Fpga;

architecture Behavioral of Intro_to_Fpga is

begin
Output1 <= NOT Input1;
Output2 <= Input1 AND Input2;
Output3 <= Input1 OR Input2;

end Behavioral;
