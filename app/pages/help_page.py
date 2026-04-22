# -*- coding: utf-8 -*-
"""使用帮助页（完全傻瓜式教程）

- 使用 QTextBrowser 展示富文本（HTML）
- 顶部章节下拉框 —— 适配较窄的 QDockWidget（默认宽度约 380px）
- 内容面向从未接触过程序的普通办公人员；站在"已通过首次设置向导完成
  初始配置"的角度撰写，不再讲手动配置的流程。

由 ``MainWindow`` 放进 :class:`PyQt5.QtWidgets.QDockWidget` 中展示，
本类不再提供返回首页的按钮/信号。

样式升级为 Neo-brutalism：奶油纸背景 + 4px 黑色边框 + 纯黑粗体字，
所有 <table>/<pre> 都强制 ``table-layout: fixed`` / ``word-wrap: break-word``
以避免在窄面板中溢出。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QTextBrowser, QVBoxLayout, QWidget
)


# 章节锚点 ID（稳定的英文 id，避免中文 fragment 问题）
SECTIONS = [
    ("sec-quick", "快速开始"),
    ("sec-tutorial", "新手实战教程"),
    ("sec-single", "创建订单"),
    ("sec-batch", "批量导入"),
    ("sec-templates", "模板管理"),
    ("sec-history", "历史记录"),
    ("sec-naming", "命名变量"),
    ("sec-faq", "常见问题"),
]


def _build_help_html() -> str:
    """构造帮助页 HTML 内容（Neo-brutalism 风格）。"""
    css = """
    <style>
      body {
        font-family: 'Space Grotesk', 'Microsoft YaHei', sans-serif;
        font-size: 14px;
        font-weight: 700;
        color: #000000;
        line-height: 1.7;
        background: #FFFDF5;
      }
      h1 {
        color: #000000;
        font-size: 22px;
        font-weight: 900;
        border-bottom: 4px solid #000000;
        padding-bottom: 6px;
        margin-top: 28px;
      }
      h2 {
        color: #000000;
        font-size: 17px;
        font-weight: 900;
        margin-top: 22px;
      }
      h3 {
        color: #000000;
        font-size: 15px;
        font-weight: 900;
        margin-top: 16px;
      }
      ol li, ul li { margin: 6px 0; }
      .note {
        background: #FFD93D;
        border: 4px solid #000000;
        padding: 10px 14px;
        margin: 12px 0;
        border-radius: 0px;
      }
      .tip {
        background: #C4B5FD;
        border: 4px solid #000000;
        padding: 10px 14px;
        margin: 12px 0;
        border-radius: 0px;
      }
      .warn {
        background: #FF6B6B;
        border: 4px solid #000000;
        padding: 10px 14px;
        margin: 12px 0;
        border-radius: 0px;
      }
      .scene {
        background: #E8F5E9;
        border: 4px solid #000000;
        padding: 10px 14px;
        margin: 12px 0;
        border-radius: 0px;
      }
      code {
        background: #FFFFFF;
        border: 2px solid #000000;
        padding: 2px 6px;
        border-radius: 0px;
        font-family: Consolas, 'Courier New', monospace;
        font-weight: 700;
      }
      .btn {
        background: #FF6B6B;
        color: #000000;
        padding: 2px 8px;
        border: 2px solid #000000;
        border-radius: 0px;
        font-weight: 900;
      }
      table {
        border-collapse: collapse;
        margin: 10px 0;
        width: 100%;
        table-layout: fixed;
      }
      th, td {
        border: 4px solid #000000;
        padding: 6px 10px;
        word-wrap: break-word;
        word-break: break-word;
      }
      th {
        background: #C4B5FD;
        color: #000000;
        font-weight: 900;
      }
      pre {
        background: #000000;
        color: #FFFDF5;
        padding: 12px;
        border: 4px solid #000000;
        border-radius: 0px;
        font-size: 13px;
        font-weight: 700;
        overflow-x: auto;
        word-wrap: break-word;
        white-space: pre-wrap;
      }
    </style>
    """

    quick = """
    <h1 id="sec-quick">第一章 · 快速开始</h1>

    <h2>首次使用（已通过向导完成）</h2>
    <p>第一次打开程序时，<b>设置向导</b>已经帮你完成了初始配置：</p>
    <ol>
      <li>选择了公司资料根目录</li>
      <li>确认了订单文件夹名称</li>
      <li>设置了产品类别（如果你们公司需要的话）</li>
      <li>导入了业务员和客户</li>
    </ol>
    <div class="tip"><b>如果需要修改这些设置</b>，随时可以在首页调整：
    <br/>· 根目录和模板目录：直接在首页顶部修改并保存
    <br/>· 订单文件夹名、中间层、产品类别：点首页底部的「⚙ 高级设置」
    <br/>· 业务员和客户：点首页的「🧭 扫描导入业务员」重新扫描</div>

    <h2>日常使用流程</h2>
    <p>设置完成后，你的日常操作只需要三步：</p>
    <ol>
      <li><b>选人、选类型</b>：在「单笔创建」页选业务员、客户、订单类型</li>
      <li><b>填订单号</b>：填上订单号，点「下一步」</li>
      <li><b>确认创建</b>：预览无误后点「确认创建」，搞定</li>
    </ol>
    <p>程序会自动帮你：建好所有文件夹、复制模板文件、生成文件清单 Excel。</p>

    <div class="note"><b>已经创建过的订单再跑一遍也不会出问题</b>——程序只会补建缺少的文件夹，
    不会覆盖或删除你已有的任何内容。</div>

    <div class="tip"><b>第一次使用？</b>强烈建议你看下一章「新手实战教程」，
    跟着虚拟场景走一遍完整流程，10 分钟就能上手！</div>
    """

    tutorial = """
    <h1 id="sec-tutorial">第二章 · 新手实战教程</h1>

    <div class="scene"><b>教程说明</b><br/>
    这一章会带你从零走完一个完整的流程。我们虚构了一个"星辰贸易公司"，
    它的文件夹结构、模板文件跟程序默认的<b>完全不一样</b>。
    跟着做一遍，你就知道怎么改成自己公司的东西了。
    <br/><br/>
    <b>你不需要真的有这家公司的文件</b>——教程会告诉你每一步在哪里点、填什么。
    如果你想跟着实际操作一遍，可以在电脑上随便建几个空文件夹和空文件来模拟。</div>

    <h2>场景设定：星辰贸易公司</h2>

    <p>星辰贸易做两种产品：<b>塑料原料</b>（江苏工厂生产）和<b>化工助剂</b>（广东工厂生产）。</p>

    <p>公司现有的文件夹结构长这样（跟程序默认的完全不同）：</p>
    <pre>D:\\星辰贸易\\
├── Orders\\                    ← 订单根文件夹（不叫"1订单"）
│   ├── 王磊\\                  ← 业务员
│   │   ├── 美国客户ABC\\       ← 客户
│   │   └── 德国客户DEF\\
│   └── 陈静\\
│       └── 日本客户GHI\\
└── 公司模板文件\\               ← 模板文件目录（不叫默认的）
    ├── 通用\\
    │   └── 采购合同.xlsx
    ├── 外贸通用\\
    │   ├── 商业发票.xlsx
    │   └── 装箱单.xlsx
    ├── 江苏工厂\\              ← 塑料原料对应的工厂
    │   ├── 江苏工厂外贸生产.xlsx
    │   └── 江苏工厂外贸发货.xlsx
    └── 广东工厂\\              ← 化工助剂对应的工厂
        ├── 广东工厂外贸生产.docx
        └── 广东工厂外贸发货.docx</pre>

    <p>每个订单创建时，公司希望的文件夹结构是这样的（也跟默认不同）：</p>
    <pre>订单号/
├── 合同单据/           ← 放采购合同、商业发票、装箱单
├── 生产跟踪/           ← 放生产通知单、发货通知单
├── 物流资料/           ← 放提单、运输文件
│   └── 报关文件/       ← 子文件夹，放报关相关
└── 质检报告/           ← 放质检文件</pre>

    <p>现在我们一步步把程序配成这样。</p>

    <h2>第 1 步：设置根目录</h2>

    <div class="note"><b>你现在要做什么：</b>告诉程序你公司的资料放在哪里。</div>

    <ol>
      <li>打开程序，看到首页</li>
      <li>在顶部找到「公司资料根目录」那一行</li>
      <li>点 <span class="btn">浏览…</span>，选择 <code>D:\\星辰贸易</code></li>
      <li>点 <span class="btn">保存</span></li>
      <li>再找到「模板文件目录」那一行</li>
      <li>点 <span class="btn">浏览…</span>，选择 <code>D:\\星辰贸易\\公司模板文件</code></li>
      <li>点 <span class="btn">保存</span></li>
    </ol>

    <div class="tip"><b>为什么要设两个目录？</b>
    <br/>· 根目录 = 你公司所有资料的总文件夹
    <br/>· 模板文件目录 = 放模板文件（空白的合同、发票等）的地方，程序会从这里复制文件到新订单里</div>

    <h2>第 2 步：修改高级设置</h2>

    <div class="note"><b>你现在要做什么：</b>告诉程序你们公司的订单文件夹叫什么名字、
    产品类别跟工厂的对应关系。</div>

    <ol>
      <li>在首页底部，点 <span class="btn">⚙ 高级设置</span></li>
      <li>找到「订单根文件夹名称」，把默认的 <code>1订单</code> 改成 <code>Orders</code>
        <br/>（因为星辰贸易的订单文件夹就叫 Orders）</li>
      <li>找到「产品类别与产地映射」表格，把默认的内容<b>全部删掉</b>，改成：
        <table>
          <tr><th>产品类别</th><th>对应产地（文件夹名）</th></tr>
          <tr><td>塑料原料</td><td>江苏工厂</td></tr>
          <tr><td>化工助剂</td><td>广东工厂</td></tr>
        </table>
      </li>
      <li>找到「产地文件扩展名映射」表格，把默认的<b>全部删掉</b>，改成：
        <table>
          <tr><th>产地/文档类型</th><th>扩展名</th></tr>
          <tr><td>江苏工厂/外贸生产</td><td>.xlsx</td></tr>
          <tr><td>江苏工厂/外贸发货</td><td>.xlsx</td></tr>
          <tr><td>广东工厂/外贸生产</td><td>.docx</td></tr>
          <tr><td>广东工厂/外贸发货</td><td>.docx</td></tr>
        </table>
      </li>
      <li>点 <span class="btn">保存</span> 关闭高级设置</li>
    </ol>

    <div class="tip"><b>这些映射是什么意思？</b>
    <br/>当你创建订单时选了「塑料原料」，程序就知道要去「江苏工厂」文件夹里找模板文件。
    <br/>选了「化工助剂」就去「广东工厂」文件夹找。就这么简单。</div>

    <h2>第 3 步：导入业务员</h2>

    <div class="note"><b>你现在要做什么：</b>让程序认识你们公司的业务员。</div>

    <ol>
      <li>回到首页，点 <span class="btn">🧭 扫描导入业务员</span></li>
      <li>程序会自动扫描 <code>D:\\星辰贸易\\Orders\\</code> 下面的文件夹</li>
      <li>你会看到列出了「王磊」和「陈静」两个文件夹</li>
      <li>勾选它们（旁边的下拉标注保持"业务员"不用改）</li>
      <li>点 <span class="btn">确认导入</span></li>
      <li>程序会自动把业务员和他们下面的客户都导进来</li>
    </ol>

    <div class="tip">导入完成后，王磊下面会自动识别出「美国客户ABC」「德国客户DEF」，
    陈静下面会识别出「日本客户GHI」。你不用手动一个个添加。</div>

    <h2>第 4 步：自定义模板结构（重点！）</h2>

    <div class="note"><b>你现在要做什么：</b>把程序默认的文件夹结构改成星辰贸易自己的结构。
    <br/>这是整个教程<b>最关键</b>的一步，也是大多数人最困惑的地方。跟紧了！</div>

    <h3>4.1 进入模板编辑器</h3>
    <ol>
      <li>点首页的 <span class="btn">🗂 模板管理</span></li>
      <li>在左边列表中，找到「公司标准·外贸」，点一下选中它</li>
      <li>点 <span class="btn">编辑</span> 按钮，进入模板编辑器</li>
    </ol>

    <h3>4.2 删掉默认的子文件夹</h3>
    <p>现在你看到左边有一棵树，里面是程序默认的文件夹结构（SD、货代资料、商检资料之类的）。
    我们要把它们<b>全部删掉</b>，换成星辰贸易自己的。</p>
    <ol>
      <li>在树上找到根节点下面的第一个子文件夹（比如 "SD"）</li>
      <li>在它上面<b>点右键</b>，选 <span class="btn">🗑 删除此节点</span></li>
      <li>如果弹出确认提示，点「是」</li>
      <li>重复上面的操作，把所有默认子文件夹全部删掉，只留下根节点（就是最顶上那个 <code>&lt;订单号&gt;</code>）</li>
    </ol>

    <div class="tip">根节点不能删除——它就是"订单号文件夹"本身，所有子文件夹都建在它下面。</div>

    <h3>4.3 添加星辰贸易的文件夹结构</h3>
    <p>现在树上只剩一个根节点了。我们来添加星辰贸易自己的结构。</p>
    <ol>
      <li>在根节点上<b>点右键</b>，选 <span class="btn">➕ 添加子文件夹</span></li>
      <li>输入名称：<code>合同单据</code>，点确定</li>
      <li>再在根节点上右键 → 添加子文件夹，输入 <code>生产跟踪</code></li>
      <li>再添加 <code>物流资料</code></li>
      <li>再添加 <code>质检报告</code></li>
      <li>现在找到刚建的「物流资料」节点，在它上面右键 → 添加子文件夹，输入 <code>报关文件</code></li>
    </ol>

    <p>现在你的树应该长这样：</p>
    <pre>&lt;订单号&gt;
├── 合同单据
├── 生产跟踪
├── 物流资料
│   └── 报关文件
└── 质检报告</pre>

    <div class="note"><b>到这一步</b>，文件夹结构已经改好了！接下来我们给每个文件夹配上要自动复制的模板文件。</div>

    <h3>4.4 给文件夹配上模板文件</h3>

    <p>我们以「合同单据」为例，演示怎么给它添加参考文件：</p>
    <ol>
      <li>在左边的树上，<b>点一下</b>「合同单据」节点（选中它）</li>
      <li>看右边，会显示这个文件夹下的文件列表（现在是空的）</li>
      <li>点右下方的 <span class="btn">+ 新增</span> 按钮，列表里出现一行新文件</li>
      <li>现在来设置这个文件的名字：
        <ul>
          <li>在文件列表中<b>点一下</b>刚新增的那一行（让它被选中）</li>
          <li>看列表上方的「常用格式」下拉框，选 <code>前缀-&lt;订单号&gt;.xlsx</code></li>
          <li>点 <span class="btn">应用格式</span></li>
          <li>弹出窗口问你输入前缀，输入 <code>采购合同</code>，点确定</li>
          <li>文件名就变成了 <code>采购合同-&lt;订单号&gt;.xlsx</code></li>
        </ul>
      </li>
      <li>现在来关联实际的模板文件：
        <ul>
          <li>确保这一行仍被选中</li>
          <li>点 <span class="btn">📂 选择模板文件</span></li>
          <li>会弹出文件选择器，自动定位到你设置的模板文件目录</li>
          <li>进入「通用」文件夹，选中 <code>采购合同.xlsx</code>，点打开</li>
          <li>右边表格的第三列「模板文件」就自动填上了路径</li>
        </ul>
      </li>
      <li>点 <span class="btn">✔ 应用修改到当前文件夹</span>（重要！不点这个改动不会生效）</li>
    </ol>

    <div class="tip"><b>总结一下刚才做了什么：</b>
    <br/>1. 给「合同单据」文件夹添加了一个文件条目
    <br/>2. 设置了它的命名规则（采购合同-订单号.xlsx）
    <br/>3. 告诉程序去哪里找模板文件原件（通用/采购合同.xlsx）
    <br/>创建订单时，程序就会自动把这个模板文件复制进去并改好名字。</div>

    <p>接下来用同样的方法给「合同单据」再添加两个文件：</p>
    <table>
      <tr><th>文件名设置</th><th>关联的模板文件</th></tr>
      <tr><td><code>商业发票-&lt;订单号&gt;.xlsx</code></td><td>外贸通用/商业发票.xlsx</td></tr>
      <tr><td><code>装箱单-&lt;订单号&gt;.xlsx</code></td><td>外贸通用/装箱单.xlsx</td></tr>
    </table>

    <p>然后点左边树上的「生产跟踪」节点，给它添加文件：</p>
    <table>
      <tr><th>文件名设置</th><th>关联的模板文件</th></tr>
      <tr><td><code>生产通知单-&lt;订单号&gt;</code>（不带扩展名！）</td><td><code>[产地]外贸生产</code>（手动输入）</td></tr>
      <tr><td><code>发货通知单-&lt;订单号&gt;</code>（不带扩展名！）</td><td><code>[产地]外贸发货</code>（手动输入）</td></tr>
    </table>

    <div class="note"><b>注意！</b>上面这两个文件比较特殊：
    <br/>· 文件名<b>没有写扩展名</b>——因为不同工厂的文件格式不一样（江苏用 .xlsx，广东用 .docx）
    <br/>· 模板文件写的是 <code>[产地]外贸生产</code>——这里的 <code>[产地]</code> 是个特殊标记
    <br/><br/>
    <b>程序会这样处理：</b>如果这笔订单的产品类别选了「塑料原料」，
    程序就把 [产地] 替换成「江苏工厂」，去找 <code>江苏工厂/江苏工厂外贸生产.xlsx</code>，
    同时自动给文件名补上 <code>.xlsx</code> 扩展名。
    <br/>如果选了「化工助剂」，就去找 <code>广东工厂/广东工厂外贸生产.docx</code>，补上 <code>.docx</code>。
    <br/><br/>
    <b>这就是为什么第 2 步要设置那些映射——它们就是在这里发挥作用的。</b></div>

    <p>「物流资料」和「质检报告」文件夹你可以暂时不添加文件（留空就行），
    或者自己练习添加。只要掌握了上面的方法，添加多少都一样。</p>

    <h3>4.5 保存模板</h3>
    <ol>
      <li>确认所有文件夹和文件都配好了</li>
      <li>点模板编辑器底部的 <span class="btn">保存</span> 按钮</li>
      <li>模板就改好了！</li>
    </ol>

    <div class="tip"><b>保存的是公司标准模板</b>，以后所有人创建外贸订单都会用这个结构。
    如果某个业务员或客户需要不一样的结构，可以「另存为业务员个人模板」或「另存为客户专属模板」。</div>

    <h2>第 5 步：创建第一笔订单！</h2>

    <div class="note"><b>你现在要做什么：</b>用刚配好的模板，创建一笔真实订单，验证一切正常。</div>

    <ol>
      <li>回到首页，点 <span class="btn">📝 单笔创建</span></li>
      <li>在上方选择：
        <ul>
          <li>业务员：<b>王磊</b></li>
          <li>客户：<b>美国客户ABC</b></li>
          <li>订单类型：<b>外贸</b></li>
          <li>产品类别：<b>塑料原料</b></li>
        </ul>
      </li>
      <li>在下方填写：
        <ul>
          <li>订单号：<code>SC-2026001</code></li>
          <li>客户名称：（已自动填好"美国客户ABC"）</li>
          <li>产品信息：<code>塑料原料PP 500KG</code>（选填）</li>
        </ul>
      </li>
      <li>点 <span class="btn">下一步：扫描并预览 →</span></li>
      <li>预览窗口里你会看到：
        <pre>📁 SC-2026001          ← 待创建（蓝色）
├── 📁 合同单据         ← 待创建
├── 📁 生产跟踪         ← 待创建
├── 📁 物流资料         ← 待创建
│   └── 📁 报关文件     ← 待创建
└── 📁 质检报告         ← 待创建</pre>
        全都是蓝色"待创建"——因为这是新订单。
      </li>
      <li>点 <span class="btn">确认创建</span></li>
    </ol>

    <h2>第 6 步：验证结果</h2>

    <p>创建完成后，打开文件管理器，去看看实际创建出来的文件夹：</p>
    <pre>D:\\星辰贸易\\Orders\\王磊\\美国客户ABC\\SC-2026001\\
├── 合同单据\\
│   ├── 采购合同-SC-2026001_对照.xlsx     ← 从 通用/采购合同.xlsx 复制来的
│   ├── 商业发票-SC-2026001_对照.xlsx     ← 从 外贸通用/商业发票.xlsx 复制来的
│   └── 装箱单-SC-2026001_对照.xlsx       ← 从 外贸通用/装箱单.xlsx 复制来的
├── 生产跟踪\\
│   ├── 生产通知单-SC-2026001_对照.xlsx   ← 从 江苏工厂/...xlsx 复制来的
│   └── 发货通知单-SC-2026001_对照.xlsx   ← 因为选了"塑料原料"→ 江苏工厂
├── 物流资料\\
│   └── 报关文件\\
├── 质检报告\\
└── 文件清单-SC-2026001.xlsx              ← 程序自动生成的勾选清单</pre>

    <div class="scene"><b>注意看：</b>
    <br/>· 文件名里的 <code>&lt;订单号&gt;</code> 已经自动替换成了 <code>SC-2026001</code>
    <br/>· 因为产品类别选了「塑料原料」→ 对应「江苏工厂」→ 所以生产跟踪里的文件是 <code>.xlsx</code> 格式
    <br/>· 如果你选的是「化工助剂」→ 对应「广东工厂」→ 文件就会是 <code>.docx</code> 格式
    <br/>· 所有文件都带了 <code>_对照</code> 后缀——这是空白模板，等你改完实际文件后可以用「整理文件夹」一键清理掉</div>

    <h2>第 7 步：日常使用（整理文件夹）</h2>

    <p>实际工作中的流程是这样的：</p>
    <ol>
      <li>程序创建了订单文件夹和空白模板文件（带 _对照）</li>
      <li>你从上一票订单文件夹里<b>复制旧文件</b>过来（比如上一票的 CI、PL 等）</li>
      <li>对照着「_对照」文件，修改旧文件里的内容（换成这一票的订单号、金额等）</li>
      <li>改完后，点创建完成界面上的 <span class="btn">🧹 整理文件夹</span></li>
      <li>程序会自动：
        <ul>
          <li>删除所有带「_对照」的空白文件</li>
          <li>把你的实际工作文件按命名规则重命名</li>
        </ul>
      </li>
      <li>确认操作列表无误后，点 <span class="btn">执行整理</span></li>
    </ol>

    <h2>教程总结</h2>

    <div class="scene"><b>恭喜！你已经完成了新手实战教程。</b>
    <br/><br/>
    回顾一下你学会了什么：
    <br/><br/>
    <b>第 1 步</b>：设置根目录和模板文件目录（告诉程序文件放在哪）
    <br/><b>第 2 步</b>：修改高级设置（订单文件夹名、产品类别映射）
    <br/><b>第 3 步</b>：导入业务员（让程序认识你们公司的人）
    <br/><b>第 4 步</b>：自定义模板结构（这是核心，决定了订单文件夹长什么样）
    <br/><b>第 5 步</b>：创建订单（日常操作就这么简单）
    <br/><b>第 6 步</b>：验证结果
    <br/><b>第 7 步</b>：整理文件夹（日常收尾操作）
    <br/><br/>
    现在你可以把教程里的"星辰贸易"换成你自己公司的真实信息，
    按同样的步骤配一遍，就完成了！
    <br/><br/>
    <b>记住最重要的一点：这个程序里没有任何东西是不可修改的。</b>
    文件夹结构、文件名、产品类别、业务员、客户——全都可以随时改。
    改错了也没关系，不会丢失你的实际文件。</div>
    """

    single = """
    <h1 id="sec-single">第三章 · 创建订单文件夹</h1>

    <h2>基本步骤</h2>
    <ol>
      <li>点首页的 <span class="btn">📝 单笔创建</span></li>
      <li>在上方选择：
        <ul>
          <li><b>业务员</b>——可以直接打字搜索</li>
          <li><b>客户</b>——也可以打字搜索，会自动过滤</li>
          <li><b>订单类型</b>：外贸或内贸</li>
          <li><b>模板</b>：程序会自动匹配，一般不用手动改</li>
          <li>如果页面上显示了<b>「产品类别」</b>下拉框，选择对应的产品类别
          （这会影响程序选用哪个工厂的模板文件）。如果没有显示这个下拉框，
          说明你们公司不需要这个功能，忽略即可。</li>
        </ul>
      </li>
      <li>在下方填写：
        <ul>
          <li><b>订单号</b>（必填）</li>
          <li><b>客户名称</b>（会根据上面的选择自动填好）</li>
          <li><b>产品信息</b>、<b>客户PO号</b>（选填）</li>
        </ul>
      </li>
      <li>外贸订单如果需要商检，勾上「需要商检资料」</li>
      <li>点 <span class="btn">下一步：扫描并预览 →</span></li>
      <li>预览窗口中：
        <table>
          <tr><th style="width:30%">颜色</th><th>含义</th></tr>
          <tr><td><b style="color:#4CAF50;">■ 绿色</b></td><td>已存在，不会重复创建</td></tr>
          <tr><td><b style="color:#2196F3;">■ 蓝色</b></td><td>不存在，程序会帮你新建</td></tr>
          <tr><td><b style="color:#9E9E9E;">■ 灰色</b></td><td>你自己建的，程序不会碰</td></tr>
        </table>
      </li>
      <li>确认后点 <span class="btn">确认创建</span>，完成！</li>
    </ol>

    <h2>整理文件夹（创建完之后用）</h2>

    <div class="tip"><b>这个功能是干什么的？</b><br/>
    创建订单后，程序会复制一些空白模板文件到文件夹里，文件名后面带「_对照」。
    这些对照文件是给你<b>参照着修改旧文件用的</b>。
    等你把上一票的文件改好之后，就可以用「整理文件夹」一键清理：
    <br/>· 删除所有带「_对照」的空白文件
    <br/>· 按命名规则给你的实际工作文件重命名</div>

    <p>具体步骤：</p>
    <ol>
      <li>创建完成后，把上一票的文件（CI、PL 等）复制到新订单文件夹里</li>
      <li>对照着「_对照」文件修改内容</li>
      <li>改完后，点 <span class="btn">🧹 整理文件夹</span></li>
      <li>程序会列出要执行的操作，逐项确认后再执行，不会不经你同意就操作</li>
    </ol>

    <h2>文件夹路径是怎么拼出来的？</h2>
    <pre>根目录 / 订单文件夹 / 业务员 / [中间层/] 客户名 / 订单号 /</pre>
    <p>举例：</p>
    <ul>
      <li>张三 + 客户A + ORD-001 → <code>根目录/订单文件夹/张三/客户A/ORD-001/</code></li>
      <li>赵六（华南分公司下）+ 客户B + ORD-002 → <code>根目录/订单文件夹/华南分公司/赵六/客户B/ORD-002/</code></li>
    </ul>
    <div class="tip">「订单文件夹」的名称和「中间层」的规则都是你在首次设置向导中确定的，
    也可以随时在「⚙ 高级设置」里修改。</div>
    """

    batch = """
    <h1 id="sec-batch">第四章 · 批量导入（一次创建多个订单）</h1>

    <ol>
      <li>点首页的 <span class="btn">📦 批量导入</span> 按钮</li>
      <li>点 <span class="btn">下载 Excel 模板</span>，保存一个 Excel 文件到电脑上</li>
      <li>用 Excel 打开这个模板文件，按表头填写每一行（<b>一行就是一笔订单</b>）：
        <table>
          <tr><th>列名</th><th>说明</th></tr>
          <tr><td>订单类型</td><td>外贸 / 内贸</td></tr>
          <tr><td>订单号</td><td>你们公司的订单编号</td></tr>
          <tr><td>客户名称</td><td>客户全称</td></tr>
          <tr><td>产品信息</td><td>选填</td></tr>
          <tr><td>客户PO号</td><td>选填</td></tr>
          <tr><td>产品类别</td><td>如果你配了产品类别，在这里填对应的类别名称；没启用这个功能的话，这一列可以留空</td></tr>
          <tr><td>是否需要商检</td><td>是 / 否（只对外贸有效）</td></tr>
          <tr><td>业务员</td><td>可选。不填时将使用页面顶部选中的业务员</td></tr>
        </table>
      </li>
      <li>保存 Excel，回到程序点 <span class="btn">导入 Excel</span>，选择刚保存的文件</li>
      <li>程序会把所有订单显示在列表里，<b>检查一遍</b>有没有填错的</li>
      <li>确认无误后，点 <span class="btn">确认批量创建</span>，程序一次性帮你创建所有订单的文件夹</li>
    </ol>

    <div class="note"><b>业务员校验：</b>
    如果 Excel 中填的业务员名字不在系统里，程序会在导入后把这些行标黄提醒你。
    建议先在首页通过「🧭 扫描导入业务员」把业务员导进来，再来做批量创建。</div>

    <div class="tip">批量创建时，每一笔订单的路径仍然按"业务员 / 客户 / 订单号"来拼接，
    与单笔创建完全一致。</div>
    """

    templates = """
    <h1 id="sec-templates">第五章 · 模板管理</h1>

    <p>这个功能用来查看和管理文件夹模板。程序内置了
       <b>外贸</b> 和 <b>内贸</b> 两套标准模板。</p>

    <h3>查看模板</h3>
    <ol>
      <li>点首页 <span class="btn">🗂 模板管理</span></li>
      <li>左边列出所有模板，点任意一个，右边显示该模板的文件夹结构树</li>
    </ol>

    <h3>另存为个人模板</h3>
    <p>如果你想在标准模板基础上做些修改（例如加一个子文件夹），可以编辑后点
      <span class="btn">另存为业务员个人模板</span>。</p>

    <h3>另存为客户专属模板</h3>
    <p>如果某个客户的订单结构比较特殊，可以编辑后点
      <span class="btn">另存为客户专属模板</span>。下次选到这个客户时，
      程序会<b>自动</b>使用这个专属模板。</p>

    <div class="warn"><b>注意：</b>公司标准模板<b>不能删除</b>，只能在其基础上另存新模板。</div>

    <h3>自定义文件命名规则</h3>
    <p>程序创建订单时，会自动给每个文件取名（例如带上订单号）。
    如果你想改变某个文件的命名方式，可以按以下步骤操作。</p>

    <div class="tip"><b>进入模板编辑器后，左边是文件夹结构树，右边是文件列表。
    双击文件名那一列就可以编辑。</b></div>

    <h3>方法一：用常用格式快速命名（最简单，推荐）</h3>
    <p>适合"前缀-订单号"这种常见命名方式。</p>
    <ol>
      <li>打开模板编辑器（在「模板管理」里选一个模板点编辑）</li>
      <li>在左边的文件夹树中，<b>点击</b>你要改的那个文件夹</li>
      <li>右边会显示这个文件夹下所有文件的列表</li>
      <li>在列表中<b>点一下</b>你要改名的那个文件（让它被选中）</li>
      <li>看右边表格上方，找到<b>「常用格式」下拉框</b></li>
      <li>从下拉框里选一个格式，比如 <code>前缀-&lt;订单号&gt;.xlsx</code></li>
      <li>点旁边的 <span class="btn">应用格式</span> 按钮</li>
      <li>会弹出一个小窗口问你：<b>「请输入前缀」</b></li>
      <li>输入你想要的前缀，例如输入 <code>CI</code>，然后点确定</li>
      <li>文件名就自动变成了 <code>CI-&lt;订单号&gt;.xlsx</code></li>
      <li>最后点 <span class="btn">✔ 应用修改到当前文件夹</span>，再点 <span class="btn">保存</span></li>
      <li>以后创建订单时，程序会自动把 <code>&lt;订单号&gt;</code> 替换成真实的订单号</li>
    </ol>
    <div class="tip"><b>总结：</b>选格式 → 输前缀 → 搞定。全程不到 5 秒。</div>

    <h3>方法二：用按钮插入占位符（适合特殊命名需求）</h3>
    <p>如果你想要的文件名不在常用格式里，比如想同时带订单号和客户名，可以这样做：</p>
    <ol>
      <li>同样在模板编辑器里，选中要改的文件</li>
      <li><b>双击</b>文件名那一格（第一列），它会变成可编辑状态</li>
      <li>先把里面的内容清空，然后手动输入你想要的固定部分</li>
      <li>然后看表格上方，有一排小按钮：
          <span class="btn">&lt;订单号&gt;</span>
          <span class="btn">&lt;客户名称&gt;</span>
          <span class="btn">&lt;客户PO号&gt;</span> 等等</li>
      <li>点一下对应按钮，程序会自动把占位符插到你的光标位置</li>
      <li>最后手动输入后缀名（比如 <code>.xlsx</code>）</li>
      <li>点 <span class="btn">✔ 应用修改到当前文件夹</span>，再点 <span class="btn">保存</span></li>
    </ol>
    <div class="note"><b>什么是占位符？</b>就是用尖括号包起来的变量名，比如 <code>&lt;订单号&gt;</code>。
    你不需要记住它们怎么写，<b>直接点按钮就行</b>，程序会自动帮你插入。
    创建订单的时候，程序会把这些占位符自动替换成真实的值。</div>

    <h3>方法三：直接手打（不推荐，容易打错）</h3>
    <p>如果你很熟悉了，也可以直接双击文件名格子，手动输入完整的命名规则，
    比如直接打 <code>CI-&lt;订单号&gt;.xlsx</code>。
    注意尖括号和里面的文字必须完全一致，打错了程序无法识别。</p>
    <p>所以<b>建议使用方法一或方法二</b>，不容易出错。</p>

    <table>
      <tr><th>占位符</th><th>会被替换成什么</th></tr>
      <tr><td><code>&lt;订单号&gt;</code></td><td>你填的订单号</td></tr>
      <tr><td><code>&lt;客户名称&gt;</code></td><td>你选的客户名称</td></tr>
      <tr><td><code>&lt;客户PO号&gt;</code></td><td>客户的PO号</td></tr>
      <tr><td><code>&lt;产品信息&gt;</code></td><td>产品信息</td></tr>
      <tr><td><code>&lt;日期&gt;</code></td><td>创建当天日期</td></tr>
      <tr><td><code>&lt;业务员&gt;</code></td><td>你选的业务员名字</td></tr>
      <tr><td><code>&lt;自定义编号&gt;</code></td><td>自定义编号（可选）</td></tr>
    </table>

    <h3>选择模板文件（新增模板不用改代码）</h3>
    <p>如果公司新增了模板文件（比如一个新的 Excel 表格），不需要改代码：</p>
    <ol>
      <li>把新模板文件放到你设置的<b>「模板文件目录」</b>里（可以建子文件夹分类）</li>
      <li>打开模板编辑器，选中对应文件夹节点，在文件列表中新增一行</li>
      <li>点 <span class="btn">📂 选择模板文件</span>，直接浏览并选择刚放进去的文件</li>
      <li>保存模板即可。以后创建订单就会自动复制这个新模板文件</li>
    </ol>
    <div class="tip">模板文件目录里放什么文件，编辑器里就能选到什么文件，完全不需要改代码。</div>
    """

    history = """
    <h1 id="sec-history">第六章 · 历史记录</h1>

    <ol>
      <li>点首页 <span class="btn">🕘 历史记录</span></li>
      <li>会显示你之前所有的创建记录</li>
      <li>可以在搜索框里输入订单号或客户名来快速查找</li>
      <li>每条记录右边有两个按钮：
        <ul>
          <li><span class="btn">详情</span>——查看这次创建的完整信息（建了哪些文件夹、复制了哪些文件）</li>
          <li><span class="btn">以此新建</span>——用这条记录的业务员、客户、订单类型等信息预填一个新订单，你只需要改订单号就行</li>
        </ul>
      </li>
    </ol>

    <div class="tip">老的历史记录（在本版本之前创建的）点「详情」只能看到统计数字，
    看不到具体的文件夹列表——这是正常现象，不影响使用。</div>
    """

    naming = """
    <h1 id="sec-naming">第七章 · 命名变量说明</h1>

    <p>在「模板管理」中编辑文件名时，可以使用以下<b>占位符</b>，
    程序在创建时会自动替换成实际内容：</p>

    <table>
      <tr><th>占位符</th><th>含义</th></tr>
      <tr><td><code>&lt;订单号&gt;</code></td><td>你填写的订单号</td></tr>
      <tr><td><code>&lt;客户名称&gt;</code></td><td>你选择的客户名称</td></tr>
      <tr><td><code>&lt;客户PO号&gt;</code></td><td>客户的采购单号（如有填）</td></tr>
      <tr><td><code>&lt;产品信息&gt;</code></td><td>产品信息（如有填）</td></tr>
      <tr><td><code>&lt;业务员&gt;</code></td><td>当前选择的业务员姓名</td></tr>
      <tr><td><code>&lt;日期&gt;</code></td><td>创建当天的日期</td></tr>
      <tr><td><code>&lt;自定义编号&gt;</code></td><td>自定义编号（可选）</td></tr>
    </table>

    <p>例如模板写 <code>CI-&lt;订单号&gt;.xlsx</code>，实际创建时会自动替换成带订单号的真实文件名。</p>

    <div class="tip">模板中还有一个特殊的 <code>[产地]</code> 标记。
    如果你在设置中配置了产品类别和工厂的对应关系，
    程序会根据当前订单的产品类别自动替换为对应工厂的模板文件。
    <br/><b>如果你没有配产品类别，这个标记不会起作用，可以忽略。</b></div>
    """

    faq = """
    <h1 id="sec-faq">第八章 · 常见问题</h1>

    <h3>Q：模板下拉框是空的怎么办？</h3>
    <p>A：检查左边的"订单类型"是不是选对了。外贸和内贸用的是不同的模板，
       切换订单类型后模板会自动更新。</p>

    <h3>Q：为什么业务员下拉框里没有人？</h3>
    <p>A：回到首页点 <span class="btn">🧭 扫描导入业务员</span> 按钮，按提示操作即可。
       也可以在创建订单页面点业务员旁边的小 <span class="btn">+</span> 按钮手动添加。</p>

    <h3>Q：创建出来的文件夹位置不对怎么办？</h3>
    <p>A：在预览界面底部有"目标路径"的显示，可以点 <span class="btn">修改…</span>
       按钮手动调整。</p>

    <h3>Q：页面上没有产品类别下拉框？</h3>
    <p>A：如果你在首次设置时选了「不需要产品类别」，这个下拉框就不会显示，这是正常的。
       如果你后来需要了，点首页底部的 <span class="btn">⚙ 高级设置</span>，
       在「产品类别与产地映射」表格中添加就行。</p>

    <h3>Q：已经创建过的订单，再跑一遍会怎样？</h3>
    <p>A：程序会自动识别已存在的文件夹（显示为绿色），<b>只补建缺失的</b>，
       不会覆盖或删除已有内容。非常安全。</p>

    <h3>Q：手动在订单文件夹下建了其它文件夹会被删除吗？</h3>
    <p>A：<b>绝对不会。</b>不在模板里的文件夹（灰色显示）程序完全不会碰它。</p>

    <h3>Q：扫描导入时，程序把分公司文件夹当成业务员了怎么办？</h3>
    <p>A：在扫描结果中找到那个文件夹，把旁边的下拉标注从"业务员"改成
       "分公司/区域（展开看子级）"，然后展开它，在里面勾选真正的业务员即可。</p>

    <h3>Q：首次设置向导填错了怎么办？</h3>
    <p>A：向导中的所有设置都可以在首页修改：
    <br/>· 根目录和模板目录：直接在首页顶部改
    <br/>· 订单文件夹名、产品类别等：点「⚙ 高级设置」
    <br/>· 业务员和客户：点「🧭 扫描导入业务员」重新扫描</p>

    <h3>Q：帮助面板挡住了操作区域怎么办？</h3>
    <p>A：你可以拖动帮助面板的边缘来调整宽度，也可以点帮助面板标题栏的 × 按钮关闭它。
    下次需要时再点页面右上角的「❓ 帮助」按钮重新打开。</p>

    <h3>Q：想给同事用这个程序，要怎么做？</h3>
    <p>A：把整个程序文件夹发给同事就行。同事打开后会弹出首次设置向导，
    按提示设置自己的根目录和导入业务员即可。</p>

    <h3>Q：我想从零搭一套跟默认完全不同的模板，怎么做？</h3>
    <p>A：请看本帮助的<b>第二章「新手实战教程」</b>，那里有完整的手把手教程，
    从一个全新的虚构公司场景出发，教你怎么把默认模板全部删掉、
    从零搭建自己的文件夹结构。</p>
    """

    parts = [css, quick, tutorial, single, batch, templates, history, naming, faq]
    return "<html><body>" + "\n".join(parts) + "</body></html>"


class HelpPage(QWidget):
    """使用帮助页。

    放入 :class:`~PyQt5.QtWidgets.QDockWidget` 中展示，
    宽度可能被压到较窄（如 380px），因此顶部导航改用
    :class:`~PyQt5.QtWidgets.QComboBox` 下拉框代替按钮组。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        title = QLabel("使用帮助")
        title.setObjectName("TitleLabel")
        root.addWidget(title)

        nav = QHBoxLayout()
        nav.setSpacing(6)
        nav.addWidget(QLabel("快速跳转："))
        self.cmb_section = QComboBox()
        for anchor, label in SECTIONS:
            self.cmb_section.addItem(label, anchor)
        self.cmb_section.currentIndexChanged.connect(self._on_section_changed)
        nav.addWidget(self.cmb_section, 1)
        root.addLayout(nav)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(_build_help_html())
        root.addWidget(self.browser, 1)

    def refresh(self):
        self.browser.verticalScrollBar().setValue(0)

    def goto_anchor(self, anchor: str):
        if not anchor:
            return
        section_label = None
        for i in range(self.cmb_section.count()):
            if self.cmb_section.itemData(i) == anchor:
                section_label = self.cmb_section.itemText(i)
                self.cmb_section.blockSignals(True)
                self.cmb_section.setCurrentIndex(i)
                self.cmb_section.blockSignals(False)
                break
        self._scroll_to_anchor_with_fallback(anchor, section_label)

    def _scroll_to_anchor_with_fallback(self, anchor: str,
                                        section_label: str = None) -> None:
        scroll_bar = self.browser.verticalScrollBar()
        old_pos = scroll_bar.value()
        self.browser.scrollToAnchor(anchor)
        new_pos = scroll_bar.value()
        if new_pos == old_pos and old_pos == 0 and section_label:
            try:
                from PyQt5.QtGui import QTextCursor
                cursor = self.browser.textCursor()
                cursor.movePosition(QTextCursor.Start)
                self.browser.setTextCursor(cursor)
                self.browser.find(section_label)
            except Exception:
                pass

    def _on_section_changed(self, idx: int):
        anchor = self.cmb_section.itemData(idx)
        if not anchor:
            return
        section_label = self.cmb_section.itemText(idx)
        self._scroll_to_anchor_with_fallback(anchor, section_label)
