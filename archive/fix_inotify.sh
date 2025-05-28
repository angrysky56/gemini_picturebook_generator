#!/bin/bash
# Fix inotify limits for Streamlit

echo "🔧 Fixing inotify limits for Streamlit..."

# Temporary fix (until reboot)
echo "Setting temporary limits..."
sudo sysctl fs.inotify.max_user_instances=512
sudo sysctl fs.inotify.max_user_watches=524288

# Permanent fix
echo "Setting permanent limits..."
echo "fs.inotify.max_user_instances=512" | sudo tee -a /etc/sysctl.conf
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf

echo "✅ inotify limits increased!"
echo "🔄 You may need to restart Streamlit apps"

# Show new limits
echo "📊 New limits:"
echo "max_user_instances: $(cat /proc/sys/fs/inotify/max_user_instances)"
echo "max_user_watches: $(cat /proc/sys/fs/inotify/max_user_watches)"
