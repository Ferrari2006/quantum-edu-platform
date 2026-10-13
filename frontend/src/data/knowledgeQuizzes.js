export const knowledgeQuizzes = {
  "what-is-quantum-computing": [
    {
      id: "scope",
      prompt: "关于量子计算，哪种说法最准确？",
      options: [
        "所有程序换到量子计算机上都会更快",
        "量子计算为特定结构的问题提供不同的求解方式",
        "量子计算只是并行运行更多经典程序",
      ],
      answer: 1,
      explanation: "量子优势只针对特定问题和算法结构，并不替代日常通用计算。",
    },
    {
      id: "resource",
      prompt: "量子算法真正设计的核心对象是什么？",
      options: ["处理器主频", "振幅、相位及其干涉", "随机数的数量"],
      answer: 1,
      explanation: "量子算法通过控制振幅与相位，让路径相互增强或抵消。",
    },
    {
      id: "boundary",
      prompt: "以下哪项更符合当前量子计算的使用方式？",
      options: ["完全取代经典计算机", "只适合网页和文档处理", "与经典计算机组成混合计算流程"],
      answer: 2,
      explanation: "现实中的量子任务通常需要经典计算机负责控制、优化和结果处理。",
    },
  ],
  "classical-bit-and-qubit": [
    {
      id: "state-description",
      prompt: "描述一个纯量子比特状态，除了测量概率还需要什么？",
      options: ["相位信息", "硬盘容量", "网络延迟"],
      answer: 0,
      explanation: "不同状态可能具有相同测量概率，却因相位不同而在后续干涉中表现不同。",
    },
    {
      id: "normalization",
      prompt: "状态 α|0⟩ + β|1⟩ 的归一化条件是什么？",
      options: ["α + β = 0", "|α|² + |β|² = 1", "α × β = 1"],
      answer: 1,
      explanation: "振幅模平方对应测量概率，所有结果的概率之和必须为1。",
    },
    {
      id: "coin-limit",
      prompt: "为什么旋转硬币不能完整代表量子比特？",
      options: ["硬币太大", "硬币类比无法表达相位和干涉", "硬币只能被测量一次"],
      answer: 1,
      explanation: "硬币能帮助理解不确定性，但无法表示复振幅与干涉。",
    },
  ],
  superposition: [
    {
      id: "amplitude",
      prompt: "振幅与普通概率最重要的区别是什么？",
      options: ["振幅可以携带符号和复相位", "振幅一定大于1", "振幅只能是整数"],
      answer: 0,
      explanation: "振幅可以相加、增强或抵消，概率则是振幅模平方后的非负实数。",
    },
    {
      id: "double-h",
      prompt: "从 |0⟩ 出发连续施加两次 H 门，理想结果是什么？",
      options: ["回到 |0⟩", "一定得到 |1⟩", "永远保持50/50随机"],
      answer: 0,
      explanation: "H·H 等于恒等操作，这个实验体现了相位和干涉，而不只是随机。",
    },
    {
      id: "value",
      prompt: "叠加产生计算价值通常还需要什么？",
      options: ["无限增加量子比特", "设计后续干涉", "立即测量每一步"],
      answer: 1,
      explanation: "只有让不同振幅路径产生有用干涉，叠加才能服务于算法目标。",
    },
  ],
  measurement: [
    {
      id: "single-shot",
      prompt: "一次计算基测量通常会返回什么？",
      options: ["完整概率分布", "一个经典结果", "所有可能结果各一次"],
      answer: 1,
      explanation: "一次实验只产生一个经典结果，概率分布需要重复准备和测量来估计。",
    },
    {
      id: "shots",
      prompt: "为什么量子实验需要多次 shots？",
      options: ["用于提高处理器频率", "用于估计结果的统计分布", "用于恢复每次测量前的同一个粒子"],
      answer: 1,
      explanation: "多次独立准备和测量得到频率，频率会逐渐接近理论概率。",
    },
    {
      id: "basis",
      prompt: "改变测量基的主要意义是什么？",
      options: ["读取状态的不同互补信息", "避免任何坍缩", "让概率总和超过1"],
      answer: 0,
      explanation: "先旋转再测量可以让原本不可见的相位关系转化为可观察结果。",
    },
  ],
  "single-qubit-gates": [
    {
      id: "x-gate",
      prompt: "X 门对计算基态做什么？",
      options: ["交换 |0⟩ 与 |1⟩", "只改变全局相位", "复制量子态"],
      answer: 0,
      explanation: "X 门类似可逆的比特翻转，会交换两个计算基态。",
    },
    {
      id: "z-gate",
      prompt: "Z 门施加后，为什么测量概率可能暂时不变？",
      options: ["Z 门什么也没做", "Z 门主要改变相对相位", "测量设备忽略所有量子门"],
      answer: 1,
      explanation: "相位通常要经过后续干涉操作，才会转化为可见的概率变化。",
    },
    {
      id: "h-gate",
      prompt: "H 门最适合用来理解哪组关系？",
      options: ["计算基与叠加基之间的转换", "不可逆的数据删除", "经典文件压缩"],
      answer: 0,
      explanation: "H 门既能从基态制造均匀叠加，也能把特定叠加转换回基态。",
    },
  ],
};

export function getKnowledgeQuiz(articleId) {
  return knowledgeQuizzes[articleId] || [];
}
