export default {
    namespaced: true,
    state: () => ({
      forwarded: null,
    }),
    mutations: {
      setForwarded(state, payload) {
        state.forwarded = payload;
      },
      clearForwarded(state) {
        state.forwarded = null;
      }
    }
  }
  