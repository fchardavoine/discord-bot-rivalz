// GitHub Repository Setup Helper
import { getUncachableGitHubClient } from './github-auth.js';

async function setupRepository() {
  try {
    const octokit = await getUncachableGitHubClient();
    
    // Get authenticated user info
    const { data: user } = await octokit.rest.users.getAuthenticated();
    console.log(`🔑 Authenticated as: ${user.login}`);
    
    // List repositories
    const { data: repos } = await octokit.rest.repos.listForAuthenticatedUser({
      sort: 'updated',
      per_page: 10
    });
    
    console.log(`\n📁 Your recent repositories:`);
    repos.forEach((repo, index) => {
      console.log(`${index + 1}. ${repo.full_name} (${repo.private ? 'private' : 'public'})`);
    });
    
    return { user, repos };
  } catch (error) {
    console.error('❌ GitHub setup error:', error.message);
  }
}

// Create a new repository for the Discord bot
async function createRepository(name = 'discord-bot-rivalz') {
  try {
    const octokit = await getUncachableGitHubClient();
    
    const { data: repo } = await octokit.rest.repos.createForAuthenticatedUser({
      name: name,
      description: 'Discord Bot with 24/7 External Restart System',
      private: false, // Set to true if you want private
      auto_init: false // We already have files
    });
    
    console.log(`✅ Repository created: ${repo.html_url}`);
    console.log(`📡 Clone URL: ${repo.clone_url}`);
    
    return repo;
  } catch (error) {
    if (error.status === 422) {
      console.log('⚠️ Repository name already exists. Try a different name.');
    } else {
      console.error('❌ Error creating repository:', error.message);
    }
  }
}

export { setupRepository, createRepository };