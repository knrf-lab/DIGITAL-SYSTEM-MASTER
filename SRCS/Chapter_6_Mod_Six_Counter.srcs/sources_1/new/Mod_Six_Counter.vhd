library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.all;
use IEEE.STD_LOGIC_UNSIGNED.all;

entity Mod_Six_Counter is
    Port (
        rst,clk : in std_logic;
        output: out std_logic_vector(2 downto 0)
    );
end Mod_Six_Counter;

architecture Behavioral of Mod_Six_Counter is

signal count : std_logic_vector(2 downto 0);

begin
    process(rst,clk)
    begin
        if (rst = '1' or count >= 6) then count <= "000";
        elsif (clk'event and clk = '1') then count <= count + 1;
        end if;
    end process;
output <= count;

end Behavioral;
