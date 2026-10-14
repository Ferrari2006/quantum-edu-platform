const dialog = document.querySelector('#play-dialog');
let opener;
document.querySelectorAll('[data-play]').forEach(button => {
  button.addEventListener('click', () => {
    opener = button;
    dialog.showModal();
  });
});
dialog.querySelector('.close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  const rect = dialog.getBoundingClientRect();
  if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
});
dialog.addEventListener('close', () => opener?.focus());
const gateData = {
 X:{title:'X 翻转炉',image:'gate-x.png',description:'交换两个基态的振幅；在布洛赫球上，对应绕 X 轴旋转半圈。',example:'从 |0⟩ 出发：X → |1⟩。再用一次 X，回到 |0⟩。'},
 H:{title:'H 分光锅',image:'gate-h.png',description:'重新组合 |0⟩ 和 |1⟩ 的振幅。从 |0⟩ 出发会得到均衡叠加；并非所有输入都会变成 50% / 50%。',example:'连续两次 H 会回到原状态：H → H，相当于什么也不做。'},
 Z:{title:'Z 调相镜',image:'gate-z.png',description:'给 |1⟩ 的振幅增加 180° 相位。当前测量概率不变，向量的 X、Y 分量会翻转。',example:'|+⟩ → |−⟩：概率都是 50% / 50%，但后续干涉的结果不同。'},
 Ry:{title:'Ry 比例调制台',image:'gate-ry.png',description:'让状态向量绕 Y 轴旋转指定角度，调制出不同的测量概率。',example:'从 |0⟩ 出发，60°、90°、120° 分别对应 P(1)=25%、50%、75%。'}
};
let amplitude0=1, amplitude1=0;
const gateHistory=[];
const byId=id=>document.getElementById(id);
function showState(){
 const p1=Math.min(1,Math.max(0,amplitude1**2)),p0=1-p1;
 const x=2*amplitude0*amplitude1,z=p0-p1;
 const negative=amplitude0*amplitude1 < -1e-8;
 byId('prob-zero').textContent=`${Math.round(p0*100)}%`;
 byId('prob-one').textContent=`${Math.round(p1*100)}%`;
 byId('meter-zero').style.width=`${p0*100}%`;byId('meter-one').style.width=`${p1*100}%`;
 const orb=byId('quantum-orb');
 const hue=215-180*p1;
 orb.style.background=`radial-gradient(circle at 30% 25%,#ffffffb8,transparent 28%),linear-gradient(125deg,hsl(${hue},75%,78%),hsl(${hue},65%,50%))`;
 orb.classList.toggle('phase-negative',negative);
 const px=130+83*x,py=125-83*z;
 byId('state-vector').setAttribute('x2',px);byId('state-vector').setAttribute('y2',py);
 byId('vector-point').setAttribute('cx',px);byId('vector-point').setAttribute('cy',py);
 const label=p1<1e-8?'|0⟩ · 静蓝球':p0<1e-8?'|1⟩ · 暖红跃金球':Math.abs(p1-.5)<1e-8?(negative?'|−⟩ · 反相同辉球':'|+⟩ · 同辉球'):'比例辉光球';
 byId('state-name').textContent=label;
 byId('relative-phase').textContent=p0<1e-8||p1<1e-8?'相对相位：不适用':`相对相位：${negative?'180°':'0°'}`;
 const fmt=n=>Math.abs(n)<1e-8?'0':n.toFixed(2);
 byId('vector-readout').textContent=`向量 (${fmt(x)}, 0, ${fmt(z)}) · 当前演示在 X–Z 平面`;
 byId('gate-history').replaceChildren();
 const base=document.createElement('span');base.textContent='|0⟩';byId('gate-history').append(base);
 for(const g of gateHistory){const tag=document.createElement('b');tag.textContent=g;byId('gate-history').append(tag)}
 if(!gateHistory.length){const text=document.createElement('span');text.textContent='· 等待操作';byId('gate-history').append(text)}
}
function applyGate(g){
 if(g==='X')[amplitude0,amplitude1]=[amplitude1,amplitude0];
 if(g==='H')[amplitude0,amplitude1]=[(amplitude0+amplitude1)*Math.SQRT1_2,(amplitude0-amplitude1)*Math.SQRT1_2];
 if(g==='Z')amplitude1=-amplitude1;
 const angle=Number(byId('ry-angle').value);
 if(g==='Ry'){const t=angle*Math.PI/360,c=Math.cos(t),s=Math.sin(t);[amplitude0,amplitude1]=[c*amplitude0-s*amplitude1,s*amplitude0+c*amplitude1]}
 const norm=Math.hypot(amplitude0,amplitude1);amplitude0/=norm;amplitude1/=norm;
 gateHistory.push(g==='Ry'?`Ry(${angle}°)`:g);showState();
}
document.querySelectorAll('[data-gate]').forEach(button=>button.addEventListener('click',()=>{
 const g=button.dataset.gate,d=gateData[g];
 document.querySelectorAll('[data-gate]').forEach(b=>b.classList.toggle('active',b===button));
 byId('gate-symbol').textContent=g;byId('gate-title').textContent=d.title;byId('gate-description').textContent=d.description;byId('gate-example').textContent=d.example;
 byId('gate-art').src=`assets/${d.image}`;byId('gate-art').alt=d.title;
 document.querySelector('.ry-control').hidden=g!=='Ry';applyGate(g);
}));
byId('reset-state').addEventListener('click',()=>{amplitude0=1;amplitude1=0;gateHistory.length=0;showState()});
showState();
