from .base import CIMObject, create_element
import uuid

class SSHProfile(CIMObject):
    def __init__(self, rdf_root):
        super().__init__(rdf_root)

    def create_terminal(self, terminal_id, cim_ns):
        terminal_element = create_element(cim_ns, "Terminal", {"rdf:about": f"#_{terminal_id}"})
        terminal_element.append(create_element(cim_ns, "ACDCTerminal.connected", text="true"))
        self.append_to_root(terminal_element)

    def create_current_limit(self, current_limit_id, cim_ns):
        current_limit_element = create_element(cim_ns, "CurrentLimit", {"rdf:about": f"#_{current_limit_id}"})
        current_limit_element.append(create_element(cim_ns, "CurrentLimit.value", text="270"))
        self.append_to_root(current_limit_element)

    def create_voltage_limit(self, voltage_limit_id, cim_ns):
        voltage_limit_element = create_element(cim_ns, "VoltageLimit", {"rdf:about": f"#_{voltage_limit_id}"})
        voltage_limit_element.append(create_element(cim_ns, "VoltageLimit.value", text="140"))
        self.append_to_root(voltage_limit_element)