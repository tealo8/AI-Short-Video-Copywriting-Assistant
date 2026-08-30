# ---------- AI 内容工场 前端镜像：构建 -> Nginx 静态托管 + API 反向代理 ----------
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
# 国内可传 --build-arg NPM_REGISTRY=https://registry.npmmirror.com
ARG NPM_REGISTRY=https://registry.npmjs.org
RUN npm install --registry=${NPM_REGISTRY}
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
