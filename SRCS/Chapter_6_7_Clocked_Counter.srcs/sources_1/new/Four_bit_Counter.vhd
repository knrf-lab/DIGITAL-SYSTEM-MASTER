library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL; 
use IEEE.STD_LOGIC_UNSIGNED.ALL; 

entity Four_bit_Counter is
    Port (
        Rst,Clk: in std_logic;
        output: out std_logic_vector(3 downto 0)
    );
end Four_bit_Counter;

architecture Behavioral of Four_bit_Counter is

signal count: std_logic_vector(3 downto 0);

begin
    process(rst,clk)
    begin
        if(rst = '1') then count <= "0000";
        elsif (clk'event and clk = '1') then count <= count + 1;
        end if;
    end process;
output <= count;

end Behavioral;
