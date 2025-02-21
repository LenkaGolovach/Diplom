<script>
export default {
  props: ['id'],
  data() {
    return {
      board: null,
      showModal: false,
      currentTask: null
    };
  },
  async created() {
    if (this.id) {
      try {
        const response = await fetch(`/api/boards/${this.id}/`);
        if (!response.ok) {
          throw new Error('Failed to load board');
        }
        this.board = await response.json();
      } catch (error) {
        toast.error('Failed to load board');
        this.$router.push('/'); // Перенаправляем на главную страницу, если доска не найдена
      }
    }
  },
  methods: {
    async updateBoardName() {
      await fetch(`/api/boards/${this.board.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.board)
      })
    },
    async addColumn() {
      const response = await fetch('/api/columns/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          board: this.board.id,
          name: 'New Column'
        })
      })
      const newColumn = await response.json()
      this.board.columns.push(newColumn)
    }
  }
}
</script>
