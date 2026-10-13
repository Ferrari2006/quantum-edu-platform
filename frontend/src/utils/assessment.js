export function scoreForm(questions, answers) {
  if (!questions.length) throw new Error("题库为空");
  const rows = questions.map(q => {
    const selected = answers[q.id];
    if (!Number.isInteger(selected) || selected < 0 || selected >= q.options.length) throw new Error("请完成全部题目");
    return { question_id: q.id, concept_id: q.concept, selected, correct: selected === q.answer };
  });
  return { correct: rows.filter(r => r.correct).length, total: rows.length, percent: rows.filter(r => r.correct).length / rows.length * 100, responses: rows };
}

export function comparison(pre, post) {
  if (!pre || !post) throw new Error("需要完整前后测");
  return { pre_percent: pre.percent, post_percent: post.percent, change_percentage_points: post.percent - pre.percent,
    interpretation: "仅描述本次分数变化，不证明游戏的因果效果；演示题未经等值与效度检验。" };
}

export function downloadJson(data, filename) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
