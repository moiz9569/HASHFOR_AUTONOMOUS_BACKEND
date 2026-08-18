---
title: SEO Auto-Fix Agent
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🚀 SEO Auto-Fix Agent

AI-powered SEO optimization that automatically fixes titles, meta descriptions, and adds structured data to your Next.js repository.

## 🔧 How to Use

1. **Add your OpenAI API key** in Space settings → Repository secrets
2. **Fill in the form** with your GitHub repository details
3. **Upload an SEO report CSV** (optional)
4. **Click "Run SEO Fix"** to automatically optimize your site

## 📋 Required Inputs

- **GitHub Token**: Personal access token with repo permissions
- **Repository URL**: Your GitHub repo URL
- **Site Base URL**: Your website's base URL
- **Branch**: Target branch (default: main)

## 🛠 Features

- ✅ AI-optimized titles & meta descriptions
- ✅ OpenGraph & Twitter Card tags
- ✅ JSON-LD structured data
- ✅ Canonical URLs & robots meta
- ✅ Automatic git commits & pushes

## 🔒 Security

Your GitHub token is used only during the process and never stored.