# 条目 × 引擎对照表（GB/T 7714-2025 corpus）

- 语料规模：28 条
- pandoc vs citeproc-py 一致（忽略空白）：5/28（一致率 17.9%）
- 差异分类计数：{'identical': 5, 'type-marker-group-dropped': 21, 'type-marker-dropped+other': 1, 'spurious-version-label': 1}
- thesisforge 手写 formatter：可渲染 16 条，无法渲染 12 条

| # | key | 目标类型 | pandoc==citeproc-py | 差异类别 | thesisforge | 备注 |
|---|-----|---------|--------------------|---------|------------|------|
| 1 | zh-article-3 | [J] | 是 | identical | 可渲染；半角标点 |  |
| 2 | zh-article-etal | [J] | 否 | type-marker-group-dropped | 可渲染；无等/et al 截断；半角标点 |  |
| 3 | en-article-etal | [J] | 否 | type-marker-group-dropped | 可渲染；无等/et al 截断；半角标点 |  |
| 4 | en-article-doi | [J] | 是 | identical | 可渲染；半角标点 |  |
| 5 | zh-article-no-volume | [J] | 否 | type-marker-group-dropped | 可渲染；半角标点 |  |
| 6 | zh-article-no-pages | [J] | 否 | type-marker-group-dropped | 可渲染；半角标点 |  |
| 7 | en-article-online-first | [J] | 是 | identical | 可渲染；半角标点 |  |
| 8 | mixed-article | [J] | 否 | type-marker-group-dropped | 可渲染；半角标点 |  |
| 9 | zh-book | [M] | 否 | type-marker-group-dropped | 可渲染；半角标点 |  |
| 10 | en-book-edition | [M] | 否 | type-marker-dropped+other | 可渲染；缺 edition；半角标点 |  |
| 11 | zh-book-translator | [M] | 否 | type-marker-group-dropped | 可渲染；缺 translator；半角标点 |  |
| 12 | org-book | [M] | 否 | type-marker-group-dropped | 可渲染；半角标点 |  |
| 13 | zh-incollection | [M] | 否 | type-marker-group-dropped | 失败：UnsupportedBibliographyTypeError |  |
| 14 | en-incollection | [M] | 否 | type-marker-group-dropped | 失败：UnsupportedBibliographyTypeError |  |
| 15 | zh-inproceedings | [C] | 否 | type-marker-group-dropped | 可渲染；半角标点 |  |
| 16 | en-inproceedings | [C] | 否 | type-marker-group-dropped | 可渲染；无等/et al 截断；半角标点 |  |
| 17 | collection-g | [G] | 否 | type-marker-group-dropped | 失败：UnsupportedBibliographyTypeError | GB/T 7714 汇编 [G]；官方 2025 CSL 无 [G] 分支（pandoc 映射为 book → [M]） |
| 18 | zh-newspaper | [N] | 否 | type-marker-group-dropped | 失败：MissingBibliographyFieldError |  |
| 19 | zh-mastersthesis | [D] | 否 | type-marker-group-dropped | 可渲染；半角标点 |  |
| 20 | zh-phdthesis | [D] | 否 | type-marker-group-dropped | 可渲染；半角标点 |  |
| 21 | zh-techreport | [R] | 否 | type-marker-group-dropped | 失败：UnsupportedBibliographyTypeError |  |
| 22 | standard-gb | [S] | 否 | type-marker-group-dropped | 失败：UnsupportedBibliographyTypeError | GB/T 7714 标准 [S]；pandoc 将 @standard 映射为 CSL legislation → 兜底 [Z] |
| 23 | zh-patent | [P] | 否 | type-marker-group-dropped | 失败：UnsupportedBibliographyTypeError |  |
| 24 | zh-online | [EB/OL] | 是 | identical | 失败：UnsupportedBibliographyTypeError |  |
| 25 | en-online-noauthor | [EB/OL] | 是 | identical | 失败：UnsupportedBibliographyTypeError |  |
| 26 | zh-dataset | [DS] | 否 | spurious-version-label | 失败：UnsupportedBibliographyTypeError |  |
| 27 | zh-map | [CM] | 否 | type-marker-group-dropped | 失败：UnsupportedBibliographyTypeError | GB/T 7714 舆图 [CM]；pandoc 不识别 @map（CSL type 为空）→ 兜底 [Z] |
| 28 | zh-archive | [A] | 否 | type-marker-group-dropped | 失败：UnsupportedBibliographyTypeError |  |

## 逐条全文对照

### [1] zh-article-3（目标 [J]）

- pandoc：`王晓明，李红霞，陈志强. 深度学习在医学影像分析中的应用[J/OL]. 中华放射学杂志，2024，58（3）：245-252. DOI:10.3760/cma.j.cn112149-20240115-00032.`
- citeproc-py：`王晓明，李红霞，陈志强. 深度学习在医学影像分析中的应用[J/OL]. 中华放射学杂志，2024，58（3）：245-252. DOI:10.3760/cma.j.cn112149-20240115-00032.`
- thesisforge：`王晓明, 李红霞, 陈志强. 深度学习在医学影像分析中的应用[J]. 中华放射学杂志, 2024, 58(3): 245-252. DOI:10.3760/cma.j.cn112149-20240115-00032.`

### [2] zh-article-etal（目标 [J]）

- pandoc：`刘洋，赵敏，孙建国，等. 城市轨道交通客流预测方法综述[J]. 交通运输工程学报，2023，23（4）：1-15.`
- citeproc-py：`刘洋，赵敏，孙建国，等. 城市轨道交通客流预测方法综述. 交通运输工程学报，2023，23（4）：1-15.`
- thesisforge：`刘洋, 赵敏, 孙建国, 周丽萍, 吴国强. 城市轨道交通客流预测方法综述[J]. 交通运输工程学报, 2023, 23(4): 1-15.`

### [3] en-article-etal（目标 [J]）

- pandoc：`Smith J，Doe J，Roe R，等. Deterministic Compilation of Academic Documents[J]. Journal of Document Engineering，2024，12（2）：101-118.`
- citeproc-py：`Smith J，Doe J，Roe R，等. Deterministic Compilation of Academic Documents. Journal of Document Engineering，2024，12（2）：101-118.`
- thesisforge：`SMITH J, DOE J, ROE R, POE A. Deterministic Compilation of Academic Documents[J]. Journal of Document Engineering, 2024, 12(2): 101-118.`

### [4] en-article-doi（目标 [J]）

- pandoc：`Brown A，Green B. Template Driven Rendering Pipelines[J/OL]. ACM Computing Surveys，2022，54（7）：1-34. DOI:10.1145/3512345.`
- citeproc-py：`Brown A，Green B. Template Driven Rendering Pipelines[J/OL]. ACM Computing Surveys，2022，54（7）：1-34. DOI:10.1145/3512345.`
- thesisforge：`BROWN A, GREEN B. Template Driven Rendering Pipelines[J]. ACM Computing Surveys, 2022, 54(7): 1-34. DOI:10.1145/3512345.`

### [5] zh-article-no-volume（目标 [J]）

- pandoc：`陈思远. 乡村教师队伍建设的路径分析[J]. 教育研究，2023（6）：88-95.`
- citeproc-py：`陈思远. 乡村教师队伍建设的路径分析. 教育研究，2023（6）：88-95.`
- thesisforge：`陈思远. 乡村教师队伍建设的路径分析[J]. 教育研究, 2023, (6): 88-95.`

### [6] zh-article-no-pages（目标 [J]）

- pandoc：`李冬梅，王海涛. 新型储能材料研究进展[J]. 材料导报，2024，38（11）.`
- citeproc-py：`李冬梅，王海涛. 新型储能材料研究进展. 材料导报，2024，38（11）.`
- thesisforge：`李冬梅, 王海涛. 新型储能材料研究进展[J]. 材料导报, 2024, 38(11).`

### [7] en-article-online-first（目标 [J]）

- pandoc：`Miller D. Citation Graph Analysis at Scale[J/OL]. Journal of Informetrics，2025. DOI:10.1016/j.joi.2025.101555.`
- citeproc-py：`Miller D. Citation Graph Analysis at Scale[J/OL]. Journal of Informetrics，2025. DOI:10.1016/j.joi.2025.101555.`
- thesisforge：`MILLER D. Citation Graph Analysis at Scale[J]. Journal of Informetrics, 2025. DOI:10.1016/j.joi.2025.101555.`

### [8] mixed-article（目标 [J]）

- pandoc：`张伟，李娜. An Efficient Algorithm for Bibliographic Parsing[J]. Chinese Journal of Computers，2023，46（9）：1901-1915.`
- citeproc-py：`张伟，李娜. An Efficient Algorithm for Bibliographic Parsing. Chinese Journal of Computers，2023，46（9）：1901-1915.`
- thesisforge：`张伟, 李娜. An Efficient Algorithm for Bibliographic Parsing[J]. Chinese Journal of Computers, 2023, 46(9): 1901-1915.`

### [9] zh-book（目标 [M]）

- pandoc：`许嘉璐. 中国古代文化常识[M]. 北京：中华书局，2020.`
- citeproc-py：`许嘉璐. 中国古代文化常识. 北京：中华书局，2020.`
- thesisforge：`许嘉璐. 中国古代文化常识[M]. 北京: 中华书局, 2020.`

### [10] en-book-edition（目标 [M]）

- pandoc：`Kuhn T S. The Structure of Scientific Revolutions[M]. 2 版. Chicago：University of Chicago Press，1970.`
- citeproc-py：`Kuhn T S. The Structure of Scientific Revolutions. 2nd 版. Chicago：University of Chicago Press，1970.`
- thesisforge：`KUHN TS. The Structure of Scientific Revolutions[M]. Chicago: University of Chicago Press, 1970.`

### [11] zh-book-translator（目标 [M]）

- pandoc：`Huntington S P. 文明的冲突与世界秩序的重建[M]. 周琪，刘绯，译. 北京：新华出版社，2010.`
- citeproc-py：`Huntington S P. 文明的冲突与世界秩序的重建. 周琪，刘绯，译. 北京：新华出版社，2010.`
- thesisforge：`HUNTINGTON SP. 文明的冲突与世界秩序的重建[M]. 北京: 新华出版社, 2010.`

### [12] org-book（目标 [M]）

- pandoc：`中华人民共和国教育部. 中国教育统计年鉴. 2022[M]. 北京：中国统计出版社，2023.`
- citeproc-py：`中华人民共和国教育部. 中国教育统计年鉴. 2022. 北京：中国统计出版社，2023.`
- thesisforge：`中华人民共和国教育部. 中国教育统计年鉴. 2022[M]. 北京: 中国统计出版社, 2023.`

### [13] zh-incollection（目标 [M]）

- pandoc：`钱钟书. 诗可以怨[M]//舒展. 钱钟书论学文选. 广州：花城出版社，1990：320-335.`
- citeproc-py：`钱钟书. 诗可以怨//舒展. 钱钟书论学文选. 广州：花城出版社，1990：320-335.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type incollection: zh-incollection

### [14] en-incollection（目标 [M]）

- pandoc：`Gamma E，Helm R. Design Patterns in Dynamic Languages[M]//Coplien J O. Pattern Languages of Program Design. Reading：Addison-Wesley，1998：55-80.`
- citeproc-py：`Gamma E，Helm R. Design Patterns in Dynamic Languages//Coplien J O. Pattern Languages of Program Design. Reading：Addison-Wesley，1998：55-80.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type incollection: en-incollection

### [15] zh-inproceedings（目标 [C]）

- pandoc：`王坚，李晓东. 大规模分布式系统的容错机制[C]//第十二届全国计算机系统结构年会论文集. 成都：电子科技大学出版社，2022：45-52.`
- citeproc-py：`王坚，李晓东. 大规模分布式系统的容错机制//第十二届全国计算机系统结构年会论文集. 成都：电子科技大学出版社，2022：45-52.`
- thesisforge：`王坚, 李晓东. 大规模分布式系统的容错机制[C]//第十二届全国计算机系统结构年会论文集. 成都: 电子科技大学出版社, 2022: 45-52.`

### [16] en-inproceedings（目标 [C]）

- pandoc：`Vaswani A，Shazeer N，Parmar N，等. Attention Is All You Need[C]//Advances in Neural Information Processing Systems 30. Long Beach，2017：5998-6008.`
- citeproc-py：`Vaswani A，Shazeer N，Parmar N，等. Attention Is All You Need//Advances in Neural Information Processing Systems 30. Long Beach，2017：5998-6008.`
- thesisforge：`VASWANI A, SHAZEER N, PARMAR N, USZKOREIT J. Attention Is All You Need[C]//Advances in Neural Information Processing Systems 30. Long Beach, 2017: 5998-6008.`

### [17] collection-g（目标 [G]）

- pandoc：`中共中央文献研究室. 建国以来重要文献选编[M]. 北京：中央文献出版社，2011.`
- citeproc-py：`中共中央文献研究室. 建国以来重要文献选编. 北京：中央文献出版社，2011.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type collection: collection-g

### [18] zh-newspaper（目标 [N]）

- pandoc：`新华社. 我国成功发射通信技术试验卫星[N]. 人民日报，2025-03-05（1）.`
- citeproc-py：`新华社. 我国成功发射通信技术试验卫星. 人民日报，2025-03-05（1）.`
- thesisforge：无法渲染 — MissingBibliographyFieldError: missing required bibliography field year: article:zh-newspaper

### [19] zh-mastersthesis（目标 [D]）

- pandoc：`刘洋. 基于深度学习的文档版面分析方法研究[D]. 北京：清华大学，2022.`
- citeproc-py：`刘洋. 基于深度学习的文档版面分析方法研究. 北京：清华大学，2022.`
- thesisforge：`刘洋. 基于深度学习的文档版面分析方法研究[D]. 北京: 清华大学, 2022.`

### [20] zh-phdthesis（目标 [D]）

- pandoc：`王慧. 中文科技论文自动文摘关键技术研究[D]. 北京：北京大学，2021.`
- citeproc-py：`王慧. 中文科技论文自动文摘关键技术研究. 北京：北京大学，2021.`
- thesisforge：`王慧. 中文科技论文自动文摘关键技术研究[D]. 北京: 北京大学, 2021.`

### [21] zh-techreport（目标 [R]）

- pandoc：`陈志明，林晓东. 高性能计算系统评测报告：ICT-TR-2023-05[R]. 北京：中国科学院计算技术研究所，2023.`
- citeproc-py：`陈志明，林晓东. 高性能计算系统评测报告：ICT-TR-2023-05. 北京：中国科学院计算技术研究所，2023.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type techreport: zh-techreport

### [22] standard-gb（目标 [S]）

- pandoc：`信息与文献 参考文献著录规则：GB/T 7714-2015[Z]. 北京：中国标准出版社，2015.`
- citeproc-py：`信息与文献 参考文献著录规则：GB/T 7714-2015. 北京：中国标准出版社，2015.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type standard: standard-gb

### [23] zh-patent（目标 [P]）

- pandoc：`华为技术有限公司. 一种文档格式转换方法及装置：CN 114567890 B[P]. 2022.`
- citeproc-py：`华为技术有限公司. 一种文档格式转换方法及装置：CN 114567890 B. 2022.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type patent: zh-patent

### [24] zh-online（目标 [EB/OL]）

- pandoc：`中国互联网络信息中心. 第53次中国互联网络发展状况统计报告[EB/OL]. （2024-03-22）[2025-06-01]. https://www.cnnic.net.cn/n4/2024/0322/c88-10964.html.`
- citeproc-py：`中国互联网络信息中心. 第53次中国互联网络发展状况统计报告[EB/OL]. （2024-03-22）[2025-06-01]. https://www.cnnic.net.cn/n4/2024/0322/c88-10964.html.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type online: zh-online

### [25] en-online-noauthor（目标 [EB/OL]）

- pandoc：`The Citation Style Language: Open Citation Formatting[EB/OL]. [2025-05-20]. https://citationstyles.org/.`
- citeproc-py：`The Citation Style Language: Open Citation Formatting[EB/OL]. [2025-05-20]. https://citationstyles.org/.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type online: en-online-noauthor

### [26] zh-dataset（目标 [DS]）

- pandoc：`国家气象信息中心. 中国地面气候资料日值数据集[DS/OL]. 国家气象科学数据中心（2020）. https://data.cma.cn/data/cdcdetail/dataCode/SURF_CLI_CHN_MUL_DAY.html.`
- citeproc-py：`国家气象信息中心. 中国地面气候资料日值数据集[DS/OL]. V. 国家气象科学数据中心（2020）. https://data.cma.cn/data/cdcdetail/dataCode/SURF_CLI_CHN_MUL_DAY.html.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type dataset: zh-dataset

### [27] zh-map（目标 [CM]）

- pandoc：`国家基础地理信息中心. 中华人民共和国全图[Z]. 北京：地图出版社，2019.`
- citeproc-py：`国家基础地理信息中心. 中华人民共和国全图. 北京：地图出版社，2019.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type map: zh-map

### [28] zh-archive（目标 [A]）

- pandoc：`国立中央研究院历史语言研究所. 明清档案：兵部题本[A]. 1932.`
- citeproc-py：`国立中央研究院历史语言研究所. 明清档案：兵部题本. 1932.`
- thesisforge：无法渲染 — UnsupportedBibliographyTypeError: unsupported bibliography type unpublished: zh-archive
