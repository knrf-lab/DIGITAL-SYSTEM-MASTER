library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Simple_Gate is
  Port ( 
      Input1: in std_logic;
      Input2: in std_logic;
      Output1: out std_logic;
      Output2: out std_logic;
      Output3: out std_logic
  );
end Simple_Gate;

architecture Behavioral of Simple_Gate is

begin
Output1 <= NOT Input1;
Output2 <= Input1 AND Input2;
Output3 <= Input1 OR Input2;

end Behavioral;
