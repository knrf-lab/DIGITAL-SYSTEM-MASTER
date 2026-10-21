library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity full_adder is
    Port (
        A,B,Cin :in STD_LOGIC;
        Cout, Sum : out STD_LOGIC
    );
end full_adder;

architecture Behavioral of full_adder is

---------half adder component---------
component half_adder is
    port (
        A,B :in STD_LOGIC;
        Cout,Sum: out STD_LOGIC
    );
end component;

--------- or gate component---------
component or_gate is
    port (
        A,B :in STD_LOGIC;
        output: out STD_LOGIC
    );
end component;
---------

signal Sum1, Cout1, Cout2: std_logic;

begin
comp1: half_adder port map(A,B,Cout1,Sum1);
comp2: half_adder port map (Sum1, Cin, Cout2, Sum);
comp3: or_gate port map (Cout1, Cout2, Cout);

end Behavioral;
