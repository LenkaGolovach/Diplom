import axios from 'axios';

class GitHubService {
  constructor() {
    // Используем CORS Anywhere как прокси для API GitHub
    this.corsProxy = 'https://cors-anywhere.herokuapp.com/';
    this.apiBaseUrl = 'https://api.github.com';
  }

  // Функция для создания моковых (тестовых) коммитов
  getTestCommits(repoName) {
    const authorNames = ['Alex Smith', 'John Doe', 'Maria Garcia', 'Sergey Ivanov', 'Zak Brown'];
    const commitMessages = [
      'Initial commit',
      'Update README.md',
      'Add basic functionality',
      'Fix bugs in main module',
      'Implement new features',
      'Refactor code',
      'Update dependencies',
      'Fix critical security issue',
      'Add tests',
      'Update documentation'
    ];
    
    // Создаем массив из 5-10 коммитов
    const count = Math.floor(Math.random() * 6) + 5;
    const result = [];
    
    for (let i = 0; i < count; i++) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      const randomAuthorIndex = Math.floor(Math.random() * authorNames.length);
      const randomMessageIndex = Math.floor(Math.random() * commitMessages.length);
      
      result.push({
        sha: `commit-${i}-${Date.now()}`,
        message: commitMessages[randomMessageIndex],
        author: {
          name: authorNames[randomAuthorIndex],
          email: `${authorNames[randomAuthorIndex].toLowerCase().replace(' ', '.')}@example.com`,
          date: date.toLocaleString(),
          avatar_url: 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
        },
        html_url: `https://github.com/${repoName}/commit/id-${i}`
      });
    }
    
    return result;
  }
  
  // Парсинг URL репозитория для получения owner/repo
  parseRepositoryUrl(url) {
    if (!url) return { owner: '', repo: '', fullName: '' };
    
    // Удаляем пробелы
    url = url.trim();
    
    // Проверяем прямой формат user/repo
    if (/^[^\/]+\/[^\/]+$/.test(url)) {
      const [owner, repo] = url.split('/');
      return {
        owner,
        repo: repo.replace(/\.git$/, ''),
        fullName: `${owner}/${repo.replace(/\.git$/, '')}`
      };
    }
    
    // Пробуем различные варианты github URL
    let match = url.match(/(?:https?:\/\/)?(?:www\.)?github\.com\/([^\/]+)\/([^\/\?\#]+)/i);
    
    if (match) {
      const [, owner, repo] = match;
      return {
        owner,
        repo: repo.replace(/\.git$/, ''),
        fullName: `${owner}/${repo.replace(/\.git$/, '')}`
      };
    }
    
    // Если не распознали, возвращаем пустые значения
    return { owner: '', repo: '', fullName: '' };
  }

  // Получение коммитов репозитория (всегда возвращает тестовые данные)
  async getCommits(fullName) {
    console.log('Загрузка коммитов для', fullName);
    
    // Проверяем кэш
    const cacheKey = `github_commits_${fullName}`;
    const cachedData = localStorage.getItem(cacheKey);
    
    if (cachedData) {
      try {
        const { data, timestamp } = JSON.parse(cachedData);
        // Используем кэш, если он не старше 1 часа
        if (Date.now() - timestamp < 3600000) {
          console.log('Возвращаем кэшированные коммиты', data);
          return data;
        }
      } catch (e) {
        console.error('Ошибка чтения кэша:', e);
      }
    }
    
    // Генерируем тестовые коммиты
    const commits = this.getTestCommits(fullName);
    
    // Кэшируем результат
    localStorage.setItem(cacheKey, JSON.stringify({
      data: commits,
      timestamp: Date.now()
    }));
    
    console.log('Сгенерированы тестовые коммиты:', commits);
    return commits;
  }

  // Получение информации о репозитории по полному имени
  async getRepository(fullName) {
    // Базовая информация о репозитории
    const [owner, repo] = fullName.split('/');
    return {
      id: Date.now(),
      name: repo,
      full_name: fullName,
      owner: { login: owner },
      html_url: `https://github.com/${fullName}`
    };
  }

  // Получение расширенной информации о репозитории
  async getRepositoryInfo(fullName) {
    // Проверяем кэш
    const cacheKey = `github_repo_info_${fullName}`;
    const cachedData = localStorage.getItem(cacheKey);
    
    if (cachedData) {
      try {
        const { data, timestamp } = JSON.parse(cachedData);
        // Используем кэш, если он не старше 1 дня
        if (Date.now() - timestamp < 86400000) {
          return data;
        }
      } catch (e) {
        console.error('Ошибка чтения кэша:', e);
      }
    }
    
    // Создаем имитацию информации о репозитории
    const [owner, repo] = fullName.split('/');
    
    // Генерируем правдоподобные даты
    const now = new Date();
    const createdAt = new Date(now);
    createdAt.setMonth(createdAt.getMonth() - Math.floor(Math.random() * 24)); // 0-24 месяца назад
    
    const updatedAt = new Date(now);
    updatedAt.setDate(updatedAt.getDate() - Math.floor(Math.random() * 30)); // 0-30 дней назад
    
    // Создаем объект с информацией
    const repoInfo = {
      id: Date.now(),
      name: repo,
      owner: owner,
      full_name: fullName,
      html_url: `https://github.com/${fullName}`,
      description: `Репозиторий ${repo}`,
      created_at: createdAt.toLocaleDateString(),
      updated_at: updatedAt.toLocaleDateString(),
      pushed_at: updatedAt.toLocaleDateString(),
      stars: Math.floor(Math.random() * 100),
      forks: Math.floor(Math.random() * 50),
      open_issues: Math.floor(Math.random() * 20),
      language: ['JavaScript', 'TypeScript', 'Python', 'Java', 'C#'][Math.floor(Math.random() * 5)]
    };
    
    // Кэшируем результат
    localStorage.setItem(cacheKey, JSON.stringify({
      data: repoInfo,
      timestamp: Date.now()
    }));
    
    return repoInfo;
  }

  // Поиск репозиториев (имитация)
  async searchRepositories(query) {
    if (!query || query.trim() === '') return [];
    
    // Проверяем кэш
    const cacheKey = `github_search_${query}`;
    const cachedData = localStorage.getItem(cacheKey);
    
    if (cachedData) {
      try {
        const { data, timestamp } = JSON.parse(cachedData);
        if (Date.now() - timestamp < 3600000) {
          return data;
        }
      } catch (e) {
        console.error('Ошибка чтения кэша:', e);
      }
    }
    
    // Генерируем тестовые результаты поиска
    const results = [
      {
        id: 1,
        name: `${query}-project`,
        full_name: `example/${query}-project`,
        description: `A sample repository matching ${query}`,
        html_url: `https://github.com/example/${query}-project`
      },
      {
        id: 2,
        name: `awesome-${query}`,
        full_name: `test-org/awesome-${query}`,
        description: `A curated list of awesome ${query} resources`,
        html_url: `https://github.com/test-org/awesome-${query}`
      },
      {
        id: 3,
        name: query,
        full_name: `github/${query}`,
        description: `Official ${query} repository`,
        html_url: `https://github.com/github/${query}`
      }
    ];
    
    // Кэшируем результат
    localStorage.setItem(cacheKey, JSON.stringify({
      data: results,
      timestamp: Date.now()
    }));
    
    return results;
  }

  // Получение Pull Requests репозитория (имитация)
  async getPullRequests(fullName) {
    // Проверяем кэш
    const cacheKey = `github_pulls_${fullName}`;
    const cachedData = localStorage.getItem(cacheKey);
    
    if (cachedData) {
      try {
        const { data, timestamp } = JSON.parse(cachedData);
        if (Date.now() - timestamp < 3600000) {
          return data;
        }
      } catch (e) {
        console.error('Ошибка чтения кэша:', e);
      }
    }
    
    // Генерируем тестовые PR
    const results = [
      {
        id: 101,
        number: 1,
        title: 'Add new feature',
        state: 'open',
        created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        updated_at: new Date(Date.now() - 86400000).toISOString(),
        user: {
          login: 'contributor1',
          avatar_url: 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
        },
        html_url: `https://github.com/${fullName}/pull/1`
      },
      {
        id: 102,
        number: 2,
        title: 'Fix bug in main module',
        state: 'closed',
        created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
        updated_at: new Date(Date.now() - 86400000 * 3).toISOString(),
        user: {
          login: 'contributor2',
          avatar_url: 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
        },
        html_url: `https://github.com/${fullName}/pull/2`
      }
    ];
    
    // Кэшируем результат
    localStorage.setItem(cacheKey, JSON.stringify({
      data: results,
      timestamp: Date.now()
    }));
    
    return results;
  }

  // Анализ URL репозитория и загрузка из него информации
  async getRepositoryFromUrl(url) {
    const { fullName } = this.parseRepositoryUrl(url);
    return this.getRepository(fullName);
  }

  // Привязка репозитория к задаче
  async linkRepository(repository, taskId) {
    try {
      // Если пришла строка URL, получаем данные репозитория
      if (typeof repository === 'string') {
        repository = await this.getRepositoryFromUrl(repository);
      }
      
      // Получаем текущий список привязанных репозиториев
      let linkedRepos = JSON.parse(localStorage.getItem('linkedRepositories') || '{}');
      
      // Добавляем новую привязку
      linkedRepos[taskId] = repository;
      
      // Сохраняем обновленный список
      localStorage.setItem('linkedRepositories', JSON.stringify(linkedRepos));
      
      // Добавляем в список недавних
      this.addToRecentRepositories(repository);
      
      return repository;
    } catch (error) {
      console.error('Ошибка привязки репозитория:', error);
      throw error;
    }
  }

  // Получение недавно использованных репозиториев
  async getRecentRepositories() {
    try {
      const recentRepos = JSON.parse(localStorage.getItem('recentRepositories') || '[]');
      return recentRepos;
    } catch (error) {
      console.error('Ошибка загрузки недавних репозиториев:', error);
      return [];
    }
  }

  // Добавление репозитория в список недавних
  addToRecentRepositories(repository) {
    try {
      let recentRepos = JSON.parse(localStorage.getItem('recentRepositories') || '[]');
      
      // Удаляем репозиторий, если он уже есть в списке
      recentRepos = recentRepos.filter(repo => repo.full_name !== repository.full_name);
      
      // Добавляем репозиторий в начало списка
      recentRepos.unshift(repository);
      
      // Ограничиваем список 10 последними репозиториями
      recentRepos = recentRepos.slice(0, 10);
      
      localStorage.setItem('recentRepositories', JSON.stringify(recentRepos));
    } catch (error) {
      console.error('Ошибка сохранения недавних репозиториев:', error);
    }
  }
}

export default new GitHubService(); 