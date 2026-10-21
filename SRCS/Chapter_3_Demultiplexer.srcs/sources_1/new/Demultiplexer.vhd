library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Demultiplexer is
  Port (
      input: in std_logic;
      selector: in std_logic_vector (2 downto 0);
      output: out std_logic_vector (7 downto 0)
  );
end Demultiplexer;

architecture Behavioral of Demultiplexer is

begin
process(input,selector)
    begin
    output <= "00000000"; 
    case selector is 
        when "000" => output(0) <= input;
        when "001" => output(1) <= input;
        when "010" => output(2) <= input;
        when "011" => output(3) <= input;
        when "100" => output(4) <= input;
        when "101" => output(5) <= input;
        when "110" => output(6) <= input;
        when "111" => output(7) <= input;
        when others => output <= "00000000";
    end case;
end process;

end Behavioral;
