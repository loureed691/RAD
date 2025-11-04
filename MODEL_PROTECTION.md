# Model Protection & Backup Guide

## 🛡️ Your Learning Data is Protected!

**TL;DR: Your ML models are SAFE from `git pull` - they will NEVER be overwritten!**

All machine learning models and training data are automatically protected by `.gitignore`. You can safely run `git pull` at any time without worrying about losing your bot's learning progress.

## Why This Matters

The RAD trading bot uses machine learning to continuously improve its trading decisions. Your bot learns from:
- Trading patterns and outcomes
- Market conditions and regimes  
- Risk management adjustments
- Feature importance and attention weights

This learning accumulates over days and weeks, making your bot progressively smarter. **Losing this data would reset all your progress!**

## How Protection Works

### Git Ignore Protection
All model files are listed in `.gitignore`:
```
models/               # Entire directory contents (except README and .gitkeep)
*.pkl                 # Joblib serialized models
*.keras               # Keras neural networks
*.h5                  # Legacy Keras format
*.pt                  # PyTorch models
*.npy                 # NumPy arrays
*.joblib              # Alternative joblib extension
models_backups/       # Your backup directory
```

### What This Means
- ✅ Your model files stay on your machine only
- ✅ `git pull` ignores model files completely
- ✅ `git push` never uploads your models
- ✅ Updates to code don't affect trained models
- ✅ Each bot instance has its own learning

## Protected Files

These files in `models/` are automatically protected:

| File | Purpose | Typical Size |
|------|---------|--------------|
| `signal_model.pkl` | ML ensemble for signal prediction | 5-10 MB |
| `deep_signal_model.keras` | Neural network for patterns | 1-5 MB |
| `q_table.pkl` | RL strategy selection | < 1 MB |
| `attention_weights.npy` | Dynamic feature weights | < 1 MB |
| `analytics_state.pkl` | Trade history & equity curve | 2-5 MB |
| `risk_manager_state.pkl` | Performance metrics | < 1 MB |

**Total: Usually less than 50 MB**

## Testing Protection

You can verify protection yourself:

```bash
# Create a test model file
echo "test data" > models/test_model.pkl

# Check git status - should be clean (file ignored)
git status

# File won't appear in changes
# This proves it's protected!

# Clean up
rm models/test_model.pkl
```

## Backup Utility

Although your models are protected from git operations, we provide a backup utility for extra safety and disaster recovery.

### Create Backup
```bash
./backup_models.sh backup
```
Creates timestamped backup in `models_backups/backup_YYYYMMDD_HHMMSS/`

### List Backups
```bash
./backup_models.sh list
```
Shows all available backups with size and file count.

### Restore Backup
```bash
# Restore latest backup
./backup_models.sh restore

# Restore specific backup
./backup_models.sh restore backup_20250101_120000
```
**Warning:** This overwrites current models - you'll be prompted to confirm.

### Cleanup Old Backups
```bash
./backup_models.sh cleanup
```
Keeps only the 5 most recent backups.

## When to Backup

### Recommended Backup Times
- ✅ Before major code updates
- ✅ Before changing bot configuration
- ✅ After significant trading sessions
- ✅ Before system maintenance
- ✅ Weekly for long-running bots

### Automatic Protection
The bot automatically:
- Saves models every 5 minutes during operation
- Saves on graceful shutdown (Ctrl+C)
- Loads saved state on startup

So you typically don't need manual backups unless you want extra safety!

## Common Scenarios

### Updating Bot Code
```bash
# No need to backup - models are protected!
git pull

# Your models remain exactly as they were
python bot.py  # Continues learning from where it left off
```

### Optional: Extra Safety Before Update
```bash
# Create backup (optional but safe)
./backup_models.sh backup

# Update code
git pull

# Models are still there, backup was precautionary
python bot.py
```

### Corrupted Model Recovery
```bash
# If a model file gets corrupted
./backup_models.sh restore

# Bot will use restored models
python bot.py
```

### Starting Fresh
```bash
# Backup current models first
./backup_models.sh backup

# Remove models to start fresh
rm models/*.pkl models/*.keras models/*.npy

# Bot creates new models from scratch
python bot.py
```

### Transferring to New Server
```bash
# On old server: create backup
./backup_models.sh backup

# Copy backup directory
scp -r models_backups/ user@newserver:/path/to/RAD/

# On new server: restore
./backup_models.sh restore
```

## Directory Structure

```
RAD/
├── models/                          # Protected by .gitignore
│   ├── .gitkeep                     # Tracked: ensures dir exists
│   ├── README.md                    # Tracked: documentation
│   ├── signal_model.pkl            # NOT tracked: your learning
│   ├── deep_signal_model.keras     # NOT tracked: your learning
│   ├── q_table.pkl                 # NOT tracked: your learning
│   ├── attention_weights.npy       # NOT tracked: your learning
│   ├── analytics_state.pkl         # NOT tracked: your learning
│   └── risk_manager_state.pkl      # NOT tracked: your learning
│
├── models_backups/                  # Protected by .gitignore
│   ├── backup_20250101_120000/     # NOT tracked: your backups
│   ├── backup_20250102_080000/     # NOT tracked: your backups
│   └── backup_20250103_150000/     # NOT tracked: your backups
│
└── backup_models.sh                 # Tracked: utility script
```

## Troubleshooting

### Q: Will `git pull` overwrite my models?
**A: No! Your models are protected by .gitignore and will never be touched by git operations.**

### Q: What if someone else commits model files?
**A: The .gitignore prevents model files from being committed in the first place. Even if someone forces a commit, your local .gitignore will protect your files during pull.**

### Q: Can I share my models with another instance?
**A: Not recommended. Each instance should learn from its own experience. Models may be overfitted to specific conditions and won't transfer well.**

### Q: How do I verify protection?
**A: Run `git check-ignore -v models/*.pkl` - should show they're ignored by .gitignore**

### Q: Models not loading after restart?
**A: Check file permissions and logs. If corrupted, use `./backup_models.sh restore` or delete the file to retrain.**

### Q: Backup directory getting large?
**A: Run `./backup_models.sh cleanup` to keep only 5 most recent backups.**

## Best Practices

1. **Trust the Protection**: Your models are safe - no need to backup before every `git pull`
2. **Periodic Backups**: Create weekly backups for long-running bots
3. **Clean Shutdown**: Always use Ctrl+C to ensure models are saved
4. **Monitor Size**: Check `models/` size if bot runs for months
5. **Test Restore**: Occasionally test backup/restore to ensure it works
6. **Document Changes**: Note when you start fresh training

## Security Notes

- Model files may contain trading history and patterns
- Keep backups secure and private
- Don't commit models to public repositories
- The `.gitignore` protects against accidental commits
- Backup directory is also protected

## Summary

✅ **Your ML models are automatically protected from git operations**  
✅ **Run `git pull` safely anytime - models won't be touched**  
✅ **Each bot instance maintains its own learning**  
✅ **Use backup utility for extra safety and disaster recovery**  
✅ **No manual steps needed - protection is automatic**

---

**You're all set! Your bot's learning is protected. Happy trading! 🚀**

For more details, see:
- `models/README.md` - Model directory documentation
- `STATE_PERSISTENCE.md` - State saving details
- `./backup_models.sh help` - Backup utility usage
