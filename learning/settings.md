# 🖥 DaVinci Resolve 极速设置（低配电脑专用）
1️⃣ 项目设置（Project Settings）
进入 Project Settings → Master Settings：
✅ Timeline Resolution → 设成 1280×720（剪辑时用低分辨率，导出前改回 1080p/4K）
✅ Timeline Frame Rate → 统一为 24fps 或 25fps（比 30/60fps 更轻松）
✅ Playback Frame Rate → 同上
✅ Video Monitoring → 设成和 Timeline 一致，不要设太高
👉 裁剪、调色时不卡，最终导出仍能用高分辨率。
2️⃣ 播放性能优化（Playback 菜单）
✅ Timeline Proxy Mode → Quarter Resolution（最低负载）
✅ Render Cache → Smart（自动缓存卡顿片段）
✅ Proxy Handling（17+ 版本） → Prefer Proxies
✅ Optimized Playback → 开启
3️⃣ 素材处理（最关键 ⚡）
先转码再导入（避免硬解压力大）：
用 Shutter Encoder / HandBrake 把素材转成 ProRes Proxy / DNxHR LB
分辨率可降到 720p 作为代理文件
或者在 Resolve 内：
右键素材 → Generate Proxy Media → 格式选 ProRes Proxy / DNxHR LB
👉 剪辑用代理，导出时切换回原片。
4️⃣ GPU / CPU 设置
Preferences → System → Memory and GPU
✅ GPU Processing Mode → CUDA（NVIDIA） / OpenCL（AMD）
✅ GPU Selection → 勾选独显（千万别只用 CPU）
内存有限时：把 “Use GPU for Blackmagic RAW decode” 关掉
5️⃣ 渲染加速技巧
右键 → Render In Place（把卡顿片段渲染成本地文件替换，不卡顿）
Delivery → Render Settings：导出时用 H.264 (MP4)，不要用 H.265（太吃性能）
剪辑时关闭：
✅ Noise Reduction（降噪）
✅ Motion Blur（运动模糊）
✅ Heavy OFX Effects（复杂插件）
6️⃣ 额外小技巧
✅ 缩小预览窗口（Program Monitor 拉小，降低解码压力）
✅ 关闭音频波形渲染（Timeline → Show Waveform 取消勾选）
✅ 缓存路径改到 SSD（Preferences → Media Storage → 设置到 SSD/NVMe 硬盘）
✅ 开启 Performance Mode（Resolve 会自动降低特效质量来保持流畅）
🚀 极速流畅工作流（推荐顺序）
新建项目时，把时间线分辨率设成 720p、帧率 24fps
导入素材 → 立即生成 代理文件（Proxy）
Playback → 设成 Quarter Resolution + Smart Cache
剪辑过程中用代理 / 优化媒体，不要开重特效
导出前 → 把 Timeline 改回 1080p/4K，并切换回原片
这样做，哪怕是 i5 + 8G 内存 + GTX 1050 这种老机器，也能勉强流畅剪辑 1080P，甚至部分 4K 素材。



# 🎬 DaVinci Resolve 不卡顿设置速查表
1️⃣ 播放性能优化
菜单路径： Playback
✅ Timeline Proxy Mode → 选择 Half Resolution 或 Quarter Resolution
✅ Render Cache → Smart（自动缓存卡顿片段） 或 User（手动缓存）
✅ Proxy Handling（17+ 版本） → Prefer Proxies
2️⃣ 生成代理 / 优化媒体
方法 1（代理）：
在 Media Pool 里右键素材 → Generate Proxy Media
格式推荐：
DNxHR LB / ProRes Proxy（流畅轻量，适合剪辑）
方法 2（优化媒体）：
Media Pool 右键 → Generate Optimized Media
格式推荐：
DNxHR SQ / ProRes 422（较高画质，适合正式剪辑）
👉 剪辑时选代理，导出时切回原素材。
3️⃣ GPU 加速设置
菜单路径： DaVinci Resolve → Preferences → System → Memory and GPU
✅ GPU Processing Mode → 选 CUDA（NVIDIA） 或 OpenCL（AMD）
✅ 勾选独显，避免只用 CPU
✅ GPU Scopes → 关闭（仅调色时再打开）
4️⃣ 时间线分辨率设置
菜单路径： Project Settings → Master Settings
Timeline Resolution：设成 1920x1080（即使素材是 4K，剪辑更流畅）
Timeline Frame Rate：统一为 24 / 25 / 30 fps（和输出需求一致即可）
Playback Frame Rate：同上
👉 最终导出时可以再改为 4K 输出，不影响质量。
5️⃣ 其他性能优化
✅ 关闭不必要的特效 / 节点（复杂调色、降噪会拖慢实时预览）
✅ 缓存到 SSD / NVMe 硬盘（优化媒体和代理尽量放在 SSD）
✅ Render In Place（右键素材 → Render In Place，直接渲染替换为可流畅播放的文件）
✅ 降低音频波形渲染：菜单 Timeline → Waveform 取消勾选
🚀 建议配置
内存：16GB 起步（4K 建议 32GB）
GPU：NVIDIA GTX1660 / RTX3060 或更高（支持 CUDA）
硬盘：NVMe SSD（缓存和代理放 SSD）
⚡ 使用顺序建议：
确定时间线分辨率（1080p 更流畅）
打开 Proxy Mode（Half/Quarter）
生成代理或优化媒体
开启 GPU 加速
如果还卡 → 用 Render Cache / Render In Place

