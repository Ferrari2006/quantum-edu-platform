import numpy as np
import random
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

class QuantumBackend:
    """
    量子游戏的底层计算引擎 (Backend)
    负责所有的矩阵运算、态矢量演化、噪声模拟以及保真度计算。
    """
    def __init__(self, num_qubits=3):
        self.num_qubits = num_qubits
        self.circuit = QuantumCircuit(self.num_qubits)
        self.current_state = None
        self.reset_circuit()

    def reset_circuit(self):
        """重置量子线路为初始基态 |00...0>"""
        self.circuit.clear()
        self.current_state = Statevector.from_instruction(self.circuit)

    def upgrade_qubits(self, new_num_qubits):
        """
        动态扩容：例如从 3 比特升级到 5 比特。
        这通常发生在切换大关卡（Ante 3）时。
        """
        print(f"[Backend] 硬件升级：量子比特数量从 {self.num_qubits} 扩容至 {new_num_qubits}")
        self.num_qubits = new_num_qubits
        self.circuit = QuantumCircuit(self.num_qubits)
        self.reset_circuit()

    def apply_gate(self, gate_type, target_qubits, theta=None):
        """
        执行量子门操作，支持单比特、双比特及多比特复合门。
        
        :param gate_type: 门类型 (如 'H', 'X', 'CNOT', 'RX', 'SWAP', 'CCX')
        :param target_qubits: 目标比特列表 (如 [0], [0, 1], 或 [0, 1, 2])
        :param theta: 连续旋转门的角度 (仅对 RX, RY, RZ 等有效)
        """
        # === 1. 单比特门 ===
        if gate_type == 'H':
            self.circuit.h(target_qubits[0])
        elif gate_type == 'X':
            self.circuit.x(target_qubits[0])
        elif gate_type == 'Y':
            self.circuit.y(target_qubits[0])
        elif gate_type == 'Z':
            self.circuit.z(target_qubits[0])
            
        # === 2. 连续旋转门 (用于金卡/蓝卡) ===
        elif gate_type == 'RX' and theta is not None:
            self.circuit.rx(theta, target_qubits[0])
        elif gate_type == 'RY' and theta is not None:
            self.circuit.ry(theta, target_qubits[0])
        elif gate_type == 'RZ' and theta is not None:
            self.circuit.rz(theta, target_qubits[0])
            
        # === 3. 双比特纠缠/交换门 ===
        elif gate_type == 'CNOT' or gate_type == 'CX':
            # target_qubits[0] 为控制位，[1] 为目标位
            self.circuit.cx(target_qubits[0], target_qubits[1])
        elif gate_type == 'SWAP':
            self.circuit.swap(target_qubits[0], target_qubits[1])
        elif gate_type == 'CZ':
            self.circuit.cz(target_qubits[0], target_qubits[1])
            
        # === 4. 三比特复合门 (大后期神牌) ===
        elif gate_type == 'CCX' or gate_type == 'TOFFOLI':
            # 两个控制位，一个目标位
            self.circuit.ccx(target_qubits[0], target_qubits[1], target_qubits[2])
        elif gate_type == 'CSWAP' or gate_type == 'FREDKIN':
            self.circuit.cswap(target_qubits[0], target_qubits[1], target_qubits[2])

        # 每次操作后，更新底层系统的状态向量
        self.current_state = Statevector.from_instruction(self.circuit)

    def inject_noise(self, intensity=0.15):
        """
        噪声注入机制：模拟退相干、热噪声或蓝卡副作用。
        通过在随机量子比特上施加一个微小的随机旋转（相干误差）来破坏保真度。
        
        :param intensity: 噪声强度，决定了随机角度的最大偏转范围。
        """
        # 随机选择一个受害的量子比特
        target = random.randint(0, self.num_qubits - 1)
        # 随机选择一种相位或翻转噪声
        noise_type = random.choice(['RX', 'RY', 'RZ'])
        # 生成一个介于 -intensity 到 +intensity 之间的微小角度
        angle = random.uniform(-intensity, intensity)
        
        if noise_type == 'RX':
            self.circuit.rx(angle, target)
        elif noise_type == 'RY':
            self.circuit.ry(angle, target)
        else:
            self.circuit.rz(angle, target)
            
        print(f"[Backend Warning] 发生量子噪声！Q{target} 发生了 {noise_type}({angle:.3f}) 的相干偏移。")
        self.current_state = Statevector.from_instruction(self.circuit)

    def calculate_fidelity(self, target_statevector):
        """
        计算保真度：当前系统态与“目标牌型态”的重合程度。
        
        :param target_statevector: Qiskit Statevector 对象，代表通关所需的目标态。
        :return: float, 0.0 到 1.0 之间。1.0 代表完美符合。
        """
        if target_statevector is None:
            return 0.0
        fidelity = state_fidelity(self.current_state, target_statevector)
        return fidelity

    def get_amplitudes(self):
        """
        获取各个基态的测量概率。
        供前端 UI 层 (Display) 调用，用于绘制概率柱状图或动态特效。
        
        :return: Numpy 1D 数组，包含每个状态的概率 (振幅绝对值的平方)。
                 长度为 2^num_qubits (3比特时为8，5比特时为32)。
        """
        return np.abs(self.current_state.data) ** 2

    def get_statevector(self):
        """返回当前的态矢量，常用于在开发阶段生成测试用的目标态"""
        return self.current_state


# ==========================================
# 简单的独立测试逻辑 (仅当你直接运行此文件时执行)
# ==========================================
if __name__ == "__main__":
    print("=== Quantum Backend 独立测试 ===")
    
    # 1. 实例化 3 比特系统
    backend = QuantumBackend(num_qubits=3)
    
    # 2. 构建一个 GHZ 态 (相当于“同花顺”目标态)
    print("\n--- 尝试构建 GHZ 态 ---")
    backend.apply_gate('H', [0])
    backend.apply_gate('CNOT', [0, 1])
    backend.apply_gate('CNOT', [1, 2])
    
    # 提取此时完美的 GHZ 态作为目标
    perfect_ghz_state = backend.get_statevector()
    print(f"完美 GHZ 态概率分布: {backend.get_amplitudes()}")
    
    # 3. 模拟玩家操作并注入噪声
    print("\n--- 玩家尝试模仿该状态，但受到噪声干扰 ---")
    backend.reset_circuit()
    backend.apply_gate('H', [0])
    # 玩家用蓝卡导致污染
    backend.inject_noise(intensity=0.4) 
    backend.apply_gate('CNOT', [0, 1])
    backend.apply_gate('CNOT', [1, 2])
    
    # 4. 计算保真度
    fid = backend.calculate_fidelity(perfect_ghz_state)
    print(f"当前态概率分布: {backend.get_amplitudes()}")
    print(f"最终判定保真度: {fid * 100:.2f}%")
    
    # 5. 测试动态扩容
    print("\n--- 进入 Boss 关卡，系统扩容 ---")
    backend.upgrade_qubits(5)
    print(f"扩容后系统基态概率分布长度: {len(backend.get_amplitudes())}")