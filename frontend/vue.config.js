module.exports = {
  publicPath: process.env.NODE_ENV === 'production' 
    ? '/' 
    : '/',
  productionSourceMap: false,
  devServer: {
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
};