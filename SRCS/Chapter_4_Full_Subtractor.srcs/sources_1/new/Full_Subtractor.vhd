library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Full_Subtractor is
    Port (
        A,B,Bin :in STD_LOGIC;
        Dif,Bout : out STD_LOGIC
    );
end Full_Subtractor;

architecture Behavioral of Full_Subtractor is

--------half subtractor component--------
component half_sub is
    port (
        A,B :in STD_LOGIC;
        Dif,Bout: out STD_LOGIC
    );
end component;

--------or gate component--------
component or_gate is
    port (
        A,B :in STD_LOGIC;
        output: out STD_LOGIC
    );
end component;

signal Dif1, Bout1, Bout2: std_logic;

begin
comp1: half_sub port map (A,B,Dif1,Bout1);
comp2: half_sub port map (Dif1,Bin,Dif,Bout2);
comp3: or_gate port map (Bout1,Bout2,Bout);

end Behavioral;

--------half subtractor program --------
library IEEE;
Use IEEE. STD_LOGIC_1164.all;

entity half_sub is
    port (
        A,B :in STD_LOGIC;
        Dif,Bout: out STD_LOGIC
    );
end half_sub;

architecture HS_arch of half_sub IS
 begin
      Dif <=  A xor B;
      Bout <= (not A) and B;
end HS_arch;

--------or gate program--------
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
