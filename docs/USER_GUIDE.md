---

## `USER_GUIDE.md`

```markdown
# User Guide – Network Speed Monitor

Welcome! This tool monitors your **real** internet speed while ignoring VPN tunnels. It helps you find out when your connection is slowest – so you can avoid those times for gaming, video calls, or large downloads.

---

## First Look

Once running (see [INSTALL.md](INSTALL.md)), open your browser to `http://localhost:3000`. You'll see:

- **Dashboard header** – shows connection health and real‑time status
- **Statistics cards** – total samples, average download/upload/latency
- **Daily Speed chart** – detailed view for a selected date
- **Weekly Trend** – stacked line chart for the last 7 days
- **Worst Performance Windows** – identifies the slowest 15‑minute periods

---

## Understanding the Charts

### Daily Speed Chart

- **Blue area** = Download speed (Mbps) – higher is better
- **Green line** = Upload speed (Mbps)
- **Orange bars** = Latency (ms) – lower is better

Use the **date picker** to view any past day. Click **Auto‑refresh** to keep the chart updated every minute.

### Weekly Trend

Shows download speed for each of the last 7 days, overlaid on the same 24‑hour timeline.

- Each day has a different colour line.
- Look for patterns: e.g., every evening around 8 PM speeds drop.

### Worst Performance Windows

The table lists the 10 slowest 15‑minute windows from the last 7 days.

- **Colour coding**:
  - Red background → `<10 Mbps` (critical)
  - Orange → `10‑25 Mbps` (poor)
  - Yellow → `25‑50 Mbps` (fair)
  - Green → `>50 Mbps` (good)

The recommendation at the bottom tells you the **single worst period** and suggests whether to reschedule heavy usage.

---

## What Does "VPN‑aware" Mean?

The poller automatically detects and **ignores** virtual adapters created by VPN software (OpenVPN, WireGuard, Cisco AnyConnect, etc.). It only measures traffic through your physical Ethernet or Wi‑Fi adapter. This gives you the true performance of your ISP and home network, without the encryption overhead or VPN server congestion.

You can verify which adapter is being used by visiting `http://localhost:8000/api/adapters`.

---

## Advanced Usage

### Export Data to CSV

1. Go to the dashboard.
2. Click the **Export** button (top right).
3. Choose start and end dates, then download the CSV file.
4. Open in Excel or any spreadsheet tool for further analysis.

### Change Polling Interval

Edit `config.ini` (in the installation folder). Set `interval_min` and `interval_max` (in minutes). Restart the service or portable script.

### Keep Data Longer

By default, data older than 30 days is automatically deleted. To keep more history, change `max_days` in `config.ini`.

---

## Frequently Asked Questions

**Q: Does this slow down my internet?**  
A: The speed test uses a small amount of bandwidth every 3‑5 minutes (similar to loading a webpage). It will not affect normal usage.

**Q: Can I run this on a laptop that moves between Wi‑Fi networks?**  
A: Yes. The poller automatically switches to the active physical adapter each time it runs.

**Q: What if I don't want any internet traffic while the test is running?**  
A: You can increase the polling interval to 10‑15 minutes in `config.ini`. You can also stop the poller service temporarily.

**Q: The worst‑time analysis shows “Not enough data”.**  
A: You need at least 2 samples in a 15‑minute window for it to appear. After 24 hours of running, you will see meaningful results.

**Q: Can I access the dashboard from another computer on my network?**  
A: By default the API binds to `127.0.0.1` (localhost only). To allow remote access, change `host = 0.0.0.0` in `config.ini` and adjust your firewall. **Do this only in trusted networks.**

---

## Support & Feedback

- **Bug reports & feature requests**: [GitHub Issues](https://github.com/yourusername/network-speed-monitor/issues)
- **Log files**: Look inside the `logs` folder – they are essential for debugging.

Thank you for using Network Speed Monitor!  
**Know your true speed, not your tunnel speed.**
