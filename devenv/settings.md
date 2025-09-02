# iphone+windows+DaVinci
# ① 录制阶段（iPhone 设置一次即可）
打开 设置 → 相机 → 格式
✅ 选 最兼容 (H.264)
❌ 不要用 HEVC/H.265（Windows 免费版达芬奇可能不支持）
打开 设置 → 相机 → 录制视频
推荐：4K / 30fps（兼容好、清晰度高、文件适中）
HDR 视频 → 关闭（避免泛白问题）
自动帧率 → 关闭
打开 设置 → 照片 → 传输到 Mac 或 PC
✅ 选 保留原片（防止自动转码压缩）
# ② 传输阶段（iPhone → Windows）
用 原装数据线 连接 iPhone 和电脑
iPhone 解锁 → 点 信任此电脑
打开 Windows 文件资源管理器 → 此电脑 → Apple iPhone → Internal Storage → DCIM
找到视频（文件名如 IMG_1234.MOV），复制到硬盘：
D:\Videos\MyProject\raw\
✅ 这样是无损原片
# ③ 达芬奇导入阶段
打开 DaVinci Resolve，新建项目
项目设置 (Project Settings → Master Settings)
Timeline Resolution：与素材一致（4K=3840×2160 / 1080p=1920×1080）
Timeline Frame Rate：与素材一致（30fps / 60fps）
Color Science：DaVinci YRGB
Timeline Color Space：Rec.709 Gamma 2.4（SDR）
在 Media Pool → 右键 → Import Media → 选择 raw 文件夹里的素材
提示是否匹配时间线 → 点 Yes
# ④ 剪辑阶段
切到 Edit 页面，开始拖拽视频到时间线
如果播放卡顿：右键视频 → Generate Optimized Media（生成代理）
常用快捷键：
I / O → 设置入点 / 出点
Ctrl + B → 切刀
Shift + Z → 缩放时间线全景
调色时：切到 Color 页面
iPhone SDR 素材：直接调整就行
如果是 HDR（忘记关）：在 Color Management 里改为 Rec.2020 → 转 SDR
# ⑤ 导出阶段
切到 Deliver 页面
常用设置：
Format：MP4
Codec：H.264（兼容性好）
Resolution：和时间线一致（4K 或 1080p）
Frame rate：和时间线一致（30fps / 60fps）
Quality：Restrict to 20,000 kb/s（4K）或 10,000 kb/s（1080p）
选保存路径 D:\Videos\MyProject\export\
Add to Render Queue → Start Render
✅ 最终效果
录制：iPhone 4K/30fps SDR 原片
传输：无损拷到 D:\Videos\MyProject\raw\
剪辑：达芬奇 SDR 流畅剪辑
导出：标准 H.264 MP4，可直接上传 B站/抖音/YouTube