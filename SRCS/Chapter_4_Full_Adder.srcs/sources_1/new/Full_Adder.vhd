library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Full_Adder is
  Port ( 
      A,B,Cin :in STD_LOGIC;
      Sum,Cout : out STD_LOGIC
  );
end Full_Adder;

architecture Behavioral of Full_Adder is

---------half adder component---------
component half_adder is
port (A,B :in STD_LOGIC;
      Sum,Cout: out STD_LOGIC);
end component;

--------- or gate component---------
component or_gate is
port (A,B :in STD_LOGIC;
      output: out STD_LOGIC);
end component;
---------

signal Sum1, Cout1, Cout2: std_logic;

begin
comp1: half_adder port map(A,B,Sum1,Cout1);
comp2: half_adder port map (Sum1, Cin, Sum, Cout2);
comp3: or_gate port map (Cout1, Cout2, Cout);

end Behavioral;

---------half adder program ---------
library IEEE;
Use IEEE. STD_LOGIC_1164.all;

entity half_adder is
    port (
        A,B : in STD_LOGIC;
        Sum,Cout : out STD_LOGIC
    );
end half_adder;

architecture HA_arch of half_adder IS
begin
    Sum <= A xor B;
    Cout <= A and B;
end HA_arch;

---------or gate program---------
library IEEE;
Use IEEE. STD_LOGIC_1164.all;

entity or_gate is
    port (
        A,B:in STD_LOGIC;
        output: out STD_LOGIC
    );
end or_gate;

architecture or_g of or_gate IS
begin
    output <= A or B;
end or_g;
