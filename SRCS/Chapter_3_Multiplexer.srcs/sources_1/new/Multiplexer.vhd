library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Multiplexer is
  Port (
      input: in std_logic_vector (3 downto 0);
      selector: in std_logic_vector (1 downto 0);
      output: out std_logic
  );
end Multiplexer;

architecture Behavioral of Multiplexer is

begin
process (input,selector)
    begin 
    case selector is
        when "00" => output <= input(0);
        when "01" => output <= input(1);
        when "10" => output <= input(2);
        when "11" => output <= input(3); 
    end case;
end process; 

end Behavioral;
