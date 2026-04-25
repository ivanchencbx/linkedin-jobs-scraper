# LinkedIn Jobs Scraper

A professional web scraping tool for extracting job listings from LinkedIn with support for authentication, pagination, and CSV storage.

## Features

- 🔐 **Secure Authentication**: Cookie-based session management with 2FA support
- 📊 **Smart Scraping**: Handles pagination and rate limiting
- 💾 **CSV Storage**: Upsert functionality to avoid duplicates
- 🎯 **Configurable Search**: Flexible job search filters
- 🚀 **Headless Support**: Can run in background
- 📝 **Comprehensive Logging**: Detailed logging for debugging
- 🛠 **Command Line Interface**: Easy to use CLI

## Installation

### From PyPI (Recommended)

```bash
pip install linkedin-jobs-scraper-cbx
```

### From Source

```bash
git clone https://github.com/yourusername/linkedin-jobs-scraper.git
cd linkedin-jobs-scraper
pip install -e .
```

## Requirements

- Python 3.8+
- Chrome browser
- ChromeDriver (automatically managed by webdriver-manager)

## Quick Start

After installation, you can run the scraper directly:

```bash
linkedin-scraper
```

Or with options:

```bash
linkedin-scraper --max-pages 5 --visible
```
Or Conduct a precise search

```bash
# 搜索中国大陆的高级Java开发工程师（最近7天，远程工作）
linkedin-scraper `
  --country 103890883 `
  --experience 5,6 `
  --function it `
  --job-type F `
  --time-range 604800 `
  --work-type 2 `
  --keywords '("Java"OR"Spring")AND("Senior"OR"Lead")AND("Developer")' `
  --sort-by R
```

## Command Line Options

| Option | Description |
| --- | --- |
| `-c`, `--config` | Path to configuration file (default: config/config.yaml) |
| `-p`, `--max-pages` | Maximum number of pages to scrape (default: all pages) |
| `--visible` | Run browser in visible mode (not headless) |
| `--refresh-session` | Refresh session and update cookies without scraping |
| `--stats` | Show statistics from CSV file |
| `--clear-cookies` | Clear saved cookies and force new login |
| `-v`, `--verbose` | Enable verbose logging |
| `-h`, `--help` | Show help message |

More options:

| 命令行参数 | 配置文件字段 | 说明 | 示例值 |
| --- | --- | --- | --- |
| `--country` 或 `--f-cr` | `f_CR` | 国家/地区ID | `102890883` (中国), `103890883` (中国大陆) |
| `--experience` 或 `--f-e` | `f_E` | 经验级别（逗号分隔） | `3,4,5,6` (3=入门,4=助理,5=高级,6=总监) |
| `--function` 或 `--f-f` | `f_F` | 职能领域 | `it`, `sales`, `marketing`, `engineering` |
| `--job-type` 或 `--f-jt` | `f_JT` | 职位类型 | `F`=全职, `C`=合同, `P`=兼职, `T`=临时, `I`=实习 |
| `--time-range` 或 `--f-tpr` | `f_TPR` | 时间范围（秒） | `604800`=7天, `2592000`=30天, `7776000`=90天 |
| `--work-type` 或 `--f-wt` | `f_WT` | 工作类型 | `1`=现场, `2`=远程, `3`=混合 |
| `--keywords` 或 `-k` | `keywords` | 搜索关键词 | `'("Python"OR"Java")AND("Developer")'` |
| `--sort-by` | `sort_by` | 排序方式 | `R`=最近, `D`=发布日期 |

## Usage Examples

### Basic Usage

```bash
# Run with default settings (will prompt for credentials on first run)
linkedin-scraper

# Scrape only first 10 pages
linkedin-scraper --max-pages 10

# Run with visible browser (useful for debugging)
linkedin-scraper --visible

# Use custom configuration file
linkedin-scraper --config /path/to/custom-config.yaml
```

### Session Management

```bash
# Refresh session and update cookies
linkedin-scraper --refresh-session

# Clear saved cookies to force new login
linkedin-scraper --clear-cookies
```

### Data Management

```bash
# Show statistics from the CSV file
linkedin-scraper --stats

# Enable verbose logging for debugging
linkedin-scraper --verbose
```

## Configuration

### First Run

The first time you run the scraper, you'll be prompted for:

- **LinkedIn email/username**: Your LinkedIn login email
- **LinkedIn password**: Your LinkedIn password (input is hidden)
- **LinkedIn display name**: Your full name as displayed on LinkedIn (case insensitive)

The display name is automatically saved to `config/config.yaml` for future use, so you won't need to enter it again.

### Configuration File

After first run, you can edit `config/config.yaml` to customize:

```yaml
# Search filters
search:
  filters:
    f_F: "it"                    # Function area
    f_CR: "102890883"            # Country/region
    f_E: "3,4,5,6"               # Experience level
    f_JT: "F"                    # Job type (F=Full-time)
    f_TPR: "2592000"             # Time range (30 days)
    f_WT: "1"                    # Work type (1=On-site)
  
  keywords: '("System"OR"Software"OR"Engineer"...)AND("Health"OR"Healthcare"OR"Medical"...)'
  sort_by: "R"                   # R=Recent, D=Date posted
  results_per_page: 25

# Browser settings
browser:
  headless: true                 # Run in background
  window_width: 1920
  window_height: 1080
  page_load_timeout: 300

# Wait times (adjust if experiencing timeouts)
waits:
  page_load: 300                 # Wait for page to load (seconds)
  element_wait: 60              # Wait for elements to appear
  verification_retry: 30        # Verification code retry interval
  between_pages: 5              # Delay between pages
```

## Project Structure

``` text
linkedin-jobs-scraper/
│
├── linkedin_scraper/                    # 主包目录
│   ├── __init__.py                      # 包初始化文件
│   ├── cli.py                           # CLI 入口点（命令行工具）
│   │
│   ├── auth/                            # 认证模块
│   │   ├── __init__.py
│   │   └── authenticator.py             # LinkedIn 认证处理
│   │
│   ├── scraper/                         # 爬取模块
│   │   ├── __init__.py
│   │   └── job_scraper.py               # 职位爬取逻辑
│   │
│   ├── storage/                         # 存储模块
│   │   ├── __init__.py
│   │   └── csv_manager.py               # CSV 文件操作
│   │
│   └── utils/                           # 工具模块
│       ├── __init__.py
│       └── helpers.py                   # 辅助函数（配置、日志等）
│
├── config/                              # 配置文件目录
│   └── config.yaml                      # 主配置文件
│
│
├── setup.py                             # PyPI 安装配置
├── pyproject.toml                       # 现代 Python 项目配置
├── requirements.txt                     # 依赖列表
├── README.md                            # 项目说明文档
├── LICENSE                              # MIT 许可证
├── MANIFEST.in                          # 打包包含的非 Python 文件
│
├── cookies.json                         # 保存的 cookies（运行时生成，不提交）
├── linkedin_jobs.csv                    # 爬取的职位数据（运行时生成，不提交）
├── scraper.log                          # 日志文件（运行时生成，不提交）
│
├── .gitignore                           # Git 忽略文件
├── .pypirc                              # PyPI 认证配置（本地，不提交）
│
└── publish.sh                           # 发布脚本（可选）

```

## Output

The scraper generates `linkedin_jobs.csv` with the following columns:

| Column | Description |
| --- | --- |
| `jobid` | Unique LinkedIn job ID |
| `jobtitle` | Job title |
| `company` | Company name |
| `location` | Job location |
| `url` | Direct link to job posting |
| `updatedatetime` | Last update timestamp |

### Sample Output

```csv
jobid,jobtitle,company,location,url,updatedatetime
4404083753,IT Business Partner,GE HealthCare,"Shanghai, Shanghai, China",https://www.linkedin.com/jobs/view/4404083753,2024-06-01 10:21:48
4404988581,Customer Program Manager-OMS,DHL Global Forwarding,"Chengdu, Sichuan, China",https://www.linkedin.com/jobs/view/4404988581,2024-06-01 10:42:44
```

## Authentication Flow

The scraper uses a smart authentication system:

1. **Cookie-based login**: Attempts to use saved cookies first (fastest)
2. **Credential-based login**: If cookies fail, uses email/password
3. **Manual intervention**: If automatic login fails, switches to visible browser for manual login
4. **2FA support**: Automatically retrieves verification codes from Gmail (requires `gog` CLI tool)

### 2FA Setup (Optional)

For automatic 2FA code retrieval, install the `gog` CLI tool:

```bash
# Install gog (Gmail CLI tool)
# Follow instructions at: https://github.com/genuinetools/gog
```

## Logging

Logs are written to `scraper.log` with the following levels:

- **INFO**: Normal operation messages
- **DEBUG**: Detailed debugging information (with `--verbose`)
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures

## Troubleshooting

### Common Issues

| Issue | Solution |
| --- | --- |
| ChromeDriver not found | Install ChromeDriver or use webdriver-manager |
| Authentication failed | Verify credentials and check 2FA setup |
| Timeout errors | Increase wait times in `config.yaml` |
| Empty search results | Check search filters and keywords |
| Cookie login fails | Run with `--clear-cookies` to force new login |

### Debug Mode

For detailed debugging:

```bash
linkedin-scraper --verbose --visible
```

### Manual Login

If automatic login keeps failing:

```bash
# Clear old cookies
linkedin-scraper --clear-cookies

# Run with visible browser
linkedin-scraper --visible
```

Then complete login manually in the browser window.

## Security

- **Passwords**: Never stored, only used during authentication
- **Cookies**: Stored locally for session management
- **Credentials**: Only email and display name are saved (display name in config)
- **2FA**: Verification codes are never stored

## Best Practices

- **Rate Limiting**: The scraper includes built-in delays to avoid being blocked
- **Session Management**: Cookies are saved to avoid frequent logins
- **Incremental Updates**: Uses upsert to avoid duplicate entries
- **Error Recovery**: Automatic retry and fallback mechanisms

## License

MIT License - see LICENSE file for details

## Disclaimer

This tool is for educational purposes only. Please respect LinkedIn's terms of service and robots.txt. Consider using LinkedIn's official API for production use. The authors are not responsible for any misuse of this tool.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- 📧 Email: <ivanchen99@gmail.com>
- 🐛 Issue Tracker: <https://github.com/ivanchencbx/linkedin-jobs-scraper/issues>
- 📖 Documentation: <https://github.com/ivanchencbx/linkedin-jobs-scraper>

## Changelog

### Version 1.0.5 (2026-04-26)

- Initial release
- Support for LinkedIn job search and scraping
- Cookie-based authentication
- CSV storage with upsert functionality
- Command-line interface
- Headless and visible browser modes
- 2FA support
