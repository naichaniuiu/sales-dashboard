const fs = require('fs');
const html = fs.readFileSync('c:/Users/wm881/WorkBuddy/20260513090923/欠款分析_客户下钻看板.html', 'utf-8');

// 检查特殊字符
const RAW = JSON.parse(html.match(/RAW = (\{[\s\S]*?\});\s*renderLevel1/)[1]);
const dangerous = [];
RAW.depts.forEach(d => {
  if (d.dept.includes("'")) dangerousNames.push('DEPT: ' + d.dept);
  (RAW.dept_sales[d.dept] || []).forEach(s => {
    if (s.name.includes("'")) dangerousNames.push('SALES: ' + d.dept + '/' + s.name);
    (s.custs || []).forEach(c => {
      if (c.name.includes("'")) dangerousNames.push('CUST: ' + d.dept + '/' + s.name + '/' + c.name);
    });
  });
});
console.log('含单引号的名称:', dangerous.length ? dangerous : '无');

// 模拟 onclick 生成
const dept = "武汉基建制造行业组";
const sales = { name: "胡松", total: 10 };
const onclick = "enterSales('" + dept + "','" + sales.name + "')";
console.log('onclick:', onclick);

// 检查脚本执行
console.log('\n=== 检查脚本结构 ===');
const lines = html.split('\n');
console.log('总行数:', lines.length);

// 找 script 标签
let inScript = false;
let scriptStart = -1;
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('<script>')) { inScript = true; scriptStart = i; }
  if (lines[i].includes('</script>')) { 
    console.log('script标签: 行', scriptStart+1, '到', i+1);
    inScript = false;
  }
}

// 输出 script 最后一行和前后几行
const lastScriptLine = html.lastIndexOf('renderLevel1');
console.log('\nrenderLevel1 附近:');
const start = Math.max(0, lastScriptLine - 50);
console.log(html.substring(start, lastScriptLine + 50));
