1️⃣ 添加 Text+ 节点
Edit 页 → 添加 Text+
进入 Fusion 页，把 Text+ 接到 MediaOut
2️⃣ Text+ → Inspector → Text
输入你要显示的文字，比如：
Hello DaVinci!
3️⃣ Write On（逐字打字）
在 Text → Write On → End → 添加表达式：
min(1, time/3)
👉 含义：
在 3 秒内打字完成
min(1, …) 让它到 1 后保持完整文字
如果要无限循环：
(time % 3) / 3
4️⃣ Size（缩放闪烁）
右键 Size → Expression：
1 + 0.2*sin(time*5)
5️⃣ Fill Color（颜色渐变）
右键 Color → Fill → Expression：
{abs(sin(time*2)), abs(sin(time*3+1)), abs(sin(time*4+2)), 1}
# 6️⃣ Center（位置浮动）
右键 Center → Expression：
{0.5 + 0.01*sin(time*3), 0.5 + 0.01*sin(time*4+1)}


{0.5 + 0.05*sin(time*0.1), 0.9+ 0.01*sin(time*0.1+1)}