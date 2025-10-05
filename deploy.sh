#!/bin/bash
#
# Automated deployment script for KuCoin Futures Trading Bot
# This script sets up the bot on a fresh Ubuntu/Debian server
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Banner
echo "================================================================"
echo "  KuCoin Futures Trading Bot - Automated Deployment"
echo "================================================================"
echo ""

# Check if running as root (we don't want that for security)
if [ "$EUID" -eq 0 ]; then 
    print_error "Please do not run this script as root"
    print_info "Run as a regular user with sudo privileges"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
print_info "Working directory: $SCRIPT_DIR"

# Step 1: Update system
print_info "Step 1/7: Updating system packages..."
sudo apt update -qq
sudo apt upgrade -y -qq
print_success "System updated"

# Step 2: Install Python 3.11 if not available
print_info "Step 2/7: Checking Python installation..."
if ! command -v python3.11 &> /dev/null; then
    print_warning "Python 3.11 not found, installing..."
    sudo apt install -y python3.11 python3.11-venv python3-pip
    print_success "Python 3.11 installed"
else
    print_success "Python 3.11 already installed"
fi

# Step 3: Install dependencies
print_info "Step 3/7: Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt" -q
print_success "Dependencies installed"

# Step 4: Create necessary directories
print_info "Step 4/7: Creating directories..."
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/models"
print_success "Directories created"

# Step 5: Setup .env file
print_info "Step 5/7: Setting up configuration..."
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    print_warning ".env file created from template"
    print_warning "⚠️  IMPORTANT: Edit .env and add your KuCoin API credentials!"
    print_info "Edit with: nano $SCRIPT_DIR/.env"
else
    print_success ".env file already exists"
fi

# Step 6: Run tests
print_info "Step 6/7: Running bot tests..."
if python3 "$SCRIPT_DIR/test_bot.py" > /dev/null 2>&1; then
    print_success "All tests passed"
else
    print_warning "Tests failed or incomplete - please check manually"
fi

# Step 7: Setup systemd service
print_info "Step 7/7: Setting up systemd service..."

# Get the current user
CURRENT_USER=$(whoami)

# Get Python path
PYTHON_PATH=$(which python3)

# Get PATH environment
USER_PATH="$PATH"

# Create service file from template
SERVICE_FILE="/tmp/kucoin-bot-$CURRENT_USER.service"
sed -e "s|%USER%|$CURRENT_USER|g" \
    -e "s|%WORKDIR%|$SCRIPT_DIR|g" \
    -e "s|%PYTHON%|$PYTHON_PATH|g" \
    -e "s|%PATH%|$USER_PATH|g" \
    "$SCRIPT_DIR/kucoin-bot.service" > "$SERVICE_FILE"

# Install service
if [ -f /etc/systemd/system/kucoin-bot.service ]; then
    print_warning "Service file already exists, backing up..."
    sudo mv /etc/systemd/system/kucoin-bot.service /etc/systemd/system/kucoin-bot.service.backup
fi

sudo mv "$SERVICE_FILE" /etc/systemd/system/kucoin-bot.service
sudo systemctl daemon-reload
print_success "Systemd service installed"

echo ""
echo "================================================================"
echo "  ✅ Deployment Complete!"
echo "================================================================"
echo ""
print_info "Next steps:"
echo ""
echo "1. Configure your API credentials:"
echo "   nano $SCRIPT_DIR/.env"
echo ""
echo "2. Enable the service to start on boot:"
echo "   sudo systemctl enable kucoin-bot"
echo ""
echo "3. Start the bot:"
echo "   sudo systemctl start kucoin-bot"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status kucoin-bot"
echo ""
echo "5. View logs:"
echo "   sudo journalctl -u kucoin-bot -f"
echo "   # or"
echo "   tail -f $SCRIPT_DIR/logs/bot.log"
echo ""
echo "================================================================"
echo ""
print_warning "IMPORTANT: Make sure to add your KuCoin API credentials to .env"
print_warning "before starting the bot!"
echo ""
