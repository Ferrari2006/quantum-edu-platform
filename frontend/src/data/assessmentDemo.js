// Wiring fixtures only. These items are NOT a validated or equated instrument.
export const assessmentDemo = {
  id: "workflow-demo", version: "0.1", status: "demo", title: "量子概念前后测 · 流程演示",
  forms: {
    pre: [
      { id: "pre-qubit", concept: "classical-bit-and-qubit", prompt: "测量一个量子比特，单次会读到什么？", options: ["一个经典结果：0或1", "所有振幅的完整列表", "同时读出0和1"], answer: 0 },
      { id: "pre-measure", concept: "measurement", prompt: "相同叠加态重复制备后测量，结果通常如何描述？", options: ["每次必定完全相同", "由概率分布描述", "与量子态无关"], answer: 1 },
    ],
    post: [
      { id: "post-qubit", concept: "classical-bit-and-qubit", prompt: "对一个量子比特做一次计算基测量，可以直接获得什么？", options: ["完整量子态", "0或1中的一个结果", "所有可能结果"], answer: 1 },
      { id: "post-measure", concept: "measurement", prompt: "多次独立制备相同量子态后测量，可以统计什么？", options: ["各结果的出现频率", "每次都相同的结果", "未知态的任意精确复制"], answer: 0 },
    ],
  },
};
