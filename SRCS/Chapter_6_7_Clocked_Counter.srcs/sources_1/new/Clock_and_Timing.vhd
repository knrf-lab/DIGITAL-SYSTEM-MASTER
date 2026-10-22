library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Clock_and_Timing is
    Port (
        source_Clk: in std_logic;
        output: out std_logic
    );
end Clock_and_Timing;

architecture Behavioral of Clock_and_Timing is

signal count : integer :=0;
signal b: std_logic :='0';

begin
    process(source_Clk)
    begin
        if(rising_edge(source_Clk)) then
        count <= count+1;
            if(count = 49999999) then
                b<=not b;
                count <=0;
            end if;
        end if;
    output <= b;
end process;

end Behavioral;
