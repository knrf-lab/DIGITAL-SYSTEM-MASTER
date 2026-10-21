library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Simple_Boolean_Algebra is
  Port ( 
    A: in std_logic;
    B: in std_logic;
    C: in std_logic;
    D: in std_logic;
    Out1: out std_logic;
    Out2: out std_logic;
    Out3: out std_logic;
    Out4: out std_logic;
    Out5: out std_logic
  );
end Simple_Boolean_Algebra;

architecture Behavioral of Simple_Boolean_Algebra is

begin
Out1 <= ((A NOR B) AND C) OR D;
Out2 <= A OR B OR C OR D;
Out3 <= A AND B AND C AND D;
Out4 <= A OR (B AND C);
Out5 <= (A AND B AND C) OR D;

end Behavioral;
