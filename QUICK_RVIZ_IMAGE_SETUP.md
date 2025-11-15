# Quick RViz Image Setup - 30 Second Guide

## 🚀 Quick Start

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
./RUN_COMPLETE_SYSTEM.sh
```

## 📺 Add Heatmap Image to RViz (5 steps)

**When RViz opens:**

1. Click **"Add"** button (bottom of Displays panel)
2. Select **"Image"** from the list → Click **"OK"**
3. Expand the new **"Image"** item
4. Set **"Image Topic"** to: `/entropy_heatmap_image`
5. Done! ✅ Image window appears with live heatmap

## 🎨 What You'll See

- 🔵 **Blue** = Low entropy (certain areas)
- 🟢 **Green/Cyan** = Medium-low entropy
- 🟡 **Yellow** = Medium entropy
- 🟠 **Orange** = Medium-high entropy
- 🔴 **Red** = High entropy (uncertain areas)

## 💡 Quick Tips

- **Resize image window**: Drag window edges
- **Toggle on/off**: Click checkbox next to "Image"
- **Save config**: File → Save Config As...

## ✅ Verify It Works

```bash
# In another terminal:
ros2 topic hz /entropy_heatmap_image
# Should show: ~10 Hz
```

## 📸 Alternative Image Viewer

```bash
ros2 run rqt_image_view rqt_image_view /entropy_heatmap_image
```

---

**Full guide**: See `ENTROPY_HEATMAP_IMAGE_SETUP.md`
