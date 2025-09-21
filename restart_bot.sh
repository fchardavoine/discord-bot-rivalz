#!/bin/bash

# Discord Bot Auto-Restart Shell Wrapper
# Provides process-level crash recovery for Reserved VM deployment

echo "🛡️ Discord Bot Auto-Restart Wrapper Started"
echo "============================================="

restart_count=0
max_restarts=1000  # Allow many restarts over time
consecutive_failures=0
max_consecutive_failures=10

while [ $restart_count -lt $max_restarts ]; do
    echo ""
    echo "🚀 Starting Discord bot (restart #${restart_count})..."
    echo "📅 $(date)"
    
    # Record start time for failure rate calculation
    start_time=$(date +%s)
    
    # Start the Python bot with repl.deploy daemon managing restarts
    ./repl.deploy python main.py
    exit_code=$?
    
    # Record end time
    end_time=$(date +%s)
    runtime=$((end_time - start_time))
    
    # Handle different exit scenarios
    if [ $exit_code -eq 0 ]; then
        echo "✅ Bot exited cleanly (exit code: 0)"
        echo "🏁 Shutdown complete"
        break
    elif [ $exit_code -eq 130 ]; then
        echo "🛑 Bot interrupted by user (Ctrl+C)"
        echo "🏁 Shutdown complete"
        break
    else
        restart_count=$((restart_count + 1))
        
        # Check if this was a quick failure (crashed within 30 seconds)
        if [ $runtime -lt 30 ]; then
            consecutive_failures=$((consecutive_failures + 1))
            echo "💥 Bot crashed quickly (${runtime}s runtime, exit code: ${exit_code})"
            echo "⚠️  Consecutive quick failures: ${consecutive_failures}/${max_consecutive_failures}"
            
            # If too many consecutive quick failures, increase delay
            if [ $consecutive_failures -ge $max_consecutive_failures ]; then
                echo "🚨 Too many consecutive quick failures, increasing restart delay"
                restart_delay=60
            else
                restart_delay=10
            fi
        else
            # Reset consecutive failures if bot ran for more than 30 seconds
            consecutive_failures=0
            restart_delay=5
            echo "💥 Bot crashed after ${runtime}s (exit code: ${exit_code})"
        fi
        
        echo "🔄 Restarting in ${restart_delay} seconds... (${restart_count}/${max_restarts})"
        sleep $restart_delay
    fi
done

# Check if we exceeded max restarts
if [ $restart_count -ge $max_restarts ]; then
    echo ""
    echo "❌ Maximum restart attempts reached (${max_restarts})"
    echo "🚨 Bot wrapper shutting down"
    exit 1
else
    echo ""
    echo "✅ Bot wrapper completed successfully"
    exit 0
fi