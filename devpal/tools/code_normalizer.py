# -*- coding: utf-8 -*-
"""
代码英文规范化工具
将代码中的中文注释、标识符转换为英文，防止 MSVC 编码错误 C4819
支持: C/C++, Python, Java, C# 等编程语言
"""
import re
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class ChineseToEnglishMapper:
    """中文字符到英文的映射器"""

    # 常见编程术语映射
    TERM_MAP: Dict[str, str] = {
        # 通用
        '用户': 'User',
        '密码': 'Password',
        '登录': 'Login',
        '注册': 'Register',
        '认证': 'Auth',
        '授权': 'Authorize',
        '会话': 'Session',
        '令牌': 'Token',
        '数据': 'Data',
        '数据库': 'Database',
        '配置': 'Config',
        '设置': 'Settings',
        '系统': 'System',
        '服务': 'Service',
        '管理器': 'Manager',
        '处理器': 'Handler',
        '控制器': 'Controller',
        '模型': 'Model',
        '视图': 'View',
        '错误': 'Error',
        '异常': 'Exception',
        '警告': 'Warning',
        '信息': 'Info',
        '日志': 'Log',
        '结果': 'Result',
        '状态': 'Status',
        '成功': 'Success',
        '失败': 'Failure',
        '有效': 'Valid',
        '无效': 'Invalid',
        '活动': 'Active',
        '锁定': 'Locked',
        '哈希': 'Hash',
        '盐': 'Salt',
        '加密': 'Encrypt',
        '解密': 'Decrypt',
        '验证': 'Verify',
        '检查': 'Check',
        '获取': 'Get',
        '设置': 'Set',
        '添加': 'Add',
        '删除': 'Delete',
        '移除': 'Remove',
        '更新': 'Update',
        '查找': 'Find',
        '搜索': 'Search',
        '创建': 'Create',
        '初始化': 'Init',
        '销毁': 'Destroy',
        '加载': 'Load',
        '保存': 'Save',
        '读取': 'Read',
        '写入': 'Write',
        '打开': 'Open',
        '关闭': 'Close',
        '开始': 'Start',
        '停止': 'Stop',
        '运行': 'Run',
        '执行': 'Execute',
        '处理': 'Process',
        '解析': 'Parse',
        '生成': 'Generate',
        '转换': 'Convert',
        '计算': 'Calculate',
        '比较': 'Compare',
        '匹配': 'Match',
        '过滤': 'Filter',
        '排序': 'Sort',
        '合并': 'Merge',
        '分割': 'Split',
        '连接': 'Connect',
        '断开': 'Disconnect',
        '发送': 'Send',
        '接收': 'Receive',
        '请求': 'Request',
        '响应': 'Response',
        '输入': 'Input',
        '输出': 'Output',
        '参数': 'Param',
        '返回': 'Return',
        '值': 'Value',
        '键': 'Key',
        '项': 'Item',
        '列表': 'List',
        '数组': 'Array',
        '映射': 'Map',
        '字典': 'Dict',
        '集合': 'Set',
        '队列': 'Queue',
        '栈': 'Stack',
        '树': 'Tree',
        '节点': 'Node',
        '指针': 'Ptr',
        '引用': 'Ref',
        '实例': 'Instance',
        '对象': 'Object',
        '类': 'Class',
        '函数': 'Func',
        '方法': 'Method',
        '成员': 'Member',
        '属性': 'Property',
        '字段': 'Field',
        '变量': 'Var',
        '常量': 'Const',
        '静态': 'Static',
        '私有': 'Private',
        '保护': 'Protected',
        '公共': 'Public',
        '内部': 'Internal',
        '外部': 'External',
        '全局': 'Global',
        '局部': 'Local',
        '临时': 'Temp',
        '缓存': 'Cache',
        '缓冲区': 'Buffer',
        '线程': 'Thread',
        '进程': 'Process',
        '互斥': 'Mutex',
        '锁': 'Lock',
        '原子': 'Atomic',
        '同步': 'Sync',
        '异步': 'Async',
        '并发': 'Concurrent',
        '并行': 'Parallel',
        '串行': 'Serial',
        '顺序': 'Order',
        '随机': 'Random',
        '唯一': 'Unique',
        '重复': 'Duplicate',
        '空': 'Null',
        '非空': 'NotNull',
        '真': 'True',
        '假': 'False',
        '是': 'Yes',
        '否': 'No',
        '和': 'And',
        '或': 'Or',
        '非': 'Not',
        '如果': 'If',
        '否则': 'Else',
        '循环': 'Loop',
        '遍历': 'Iterate',
        '迭代': 'Iterator',
        '索引': 'Index',
        '大小': 'Size',
        '长度': 'Length',
        '容量': 'Capacity',
        '计数': 'Count',
        '数量': 'Amount',
        '总数': 'Total',
        '当前': 'Current',
        '上一个': 'Prev',
        '下一个': 'Next',
        '第一个': 'First',
        '最后一个': 'Last',
        '最大': 'Max',
        '最小': 'Min',
        '平均': 'Avg',
        '总和': 'Sum',
        '百分比': 'Percent',
        '比例': 'Ratio',
        '速率': 'Rate',
        '时间': 'Time',
        '日期': 'Date',
        '时间戳': 'Timestamp',
        '超时': 'Timeout',
        '过期': 'Expire',
        '有效期': 'Expiration',
        '路径': 'Path',
        '文件': 'File',
        '目录': 'Dir',
        '文件夹': 'Folder',
        '名称': 'Name',
        '标识': 'Id',
        '编号': 'Num',
        '版本': 'Version',
        '类型': 'Type',
        '种类': 'Kind',
        '模式': 'Mode',
        '标志': 'Flag',
        '选项': 'Option',
        '特性': 'Feature',
        '功能': 'Func',
        '操作': 'Op',
        '动作': 'Action',
        '事件': 'Event',
        '消息': 'Message',
        '通知': 'Notify',
        '回调': 'Callback',
        '委托': 'Delegate',
        '接口': 'Interface',
        '实现': 'Impl',
        '继承': 'Inherit',
        '派生': 'Derived',
        '基类': 'Base',
        '父类': 'Parent',
        '子类': 'Child',
        '抽象': 'Abstract',
        '虚拟': 'Virtual',
        '覆盖': 'Override',
        '重载': 'Overload',
        '模板': 'Template',
        '泛型': 'Generic',
        '宏': 'Macro',
        '定义': 'Define',
        '声明': 'Declare',
        '包含': 'Include',
        '导入': 'Import',
        '导出': 'Export',
        '模块': 'Module',
        '包': 'Package',
        '命名空间': 'Namespace',
        '作用域': 'Scope',
        '上下文': 'Context',
        '环境': 'Env',
        '构建': 'Build',
        '编译': 'Compile',
        '链接': 'Link',
        '链接器': 'Linker',
        '调试': 'Debug',
        '发布': 'Release',
        '性能': 'Performance',
        '优化': 'Optimize',
        '内存': 'Memory',
        '堆': 'Heap',
        '栈': 'Stack',
        '分配': 'Alloc',
        '释放': 'Free',
        '泄漏': 'Leak',
        '溢出': 'Overflow',
        '边界': 'Boundary',
        '限制': 'Limit',
        '最大': 'Max',
        '最小': 'Min',
        '范围': 'Range',
        '区间': 'Interval',
        '级别': 'Level',
        '优先级': 'Priority',
        '策略': 'Strategy',
        '算法': 'Algorithm',
        '规则': 'Rule',
        '标准': 'Standard',
        '协议': 'Protocol',
        '格式': 'Format',
        '编码': 'Encoding',
        '解码': 'Decoding',
        '压缩': 'Compress',
        '解压': 'Decompress',
        '序列化': 'Serialize',
        '反序列化': 'Deserialize',
        'JSON': 'JSON',
        'XML': 'XML',
        'YAML': 'YAML',
        'CSV': 'CSV',
        '文本': 'Text',
        '二进制': 'Binary',
        '流': 'Stream',
        '通道': 'Channel',
        '管道': 'Pipe',
        '套接字': 'Socket',
        '端口': 'Port',
        '地址': 'Addr',
        '主机': 'Host',
        '服务器': 'Server',
        '客户端': 'Client',
        '网络': 'Network',
        '连接': 'Connection',
        '会话': 'Session',
        '事务': 'Transaction',
        '提交': 'Commit',
        '回滚': 'Rollback',
        'ACID': 'ACID',
        '原子性': 'Atomicity',
        '一致性': 'Consistency',
        '隔离性': 'Isolation',
        '持久性': 'Durability',
        '查询': 'Query',
        '命令': 'Command',
        '语句': 'Statement',
        '表': 'Table',
        '行': 'Row',
        '列': 'Column',
        '记录': 'Record',
        '字段': 'Field',
        '主键': 'PrimaryKey',
        '外键': 'ForeignKey',
        '索引': 'Index',
        '视图': 'View',
        '存储过程': 'StoredProcedure',
        '触发器': 'Trigger',
        '游标': 'Cursor',
        '事务': 'Transaction',
        '备份': 'Backup',
        '恢复': 'Restore',
        '迁移': 'Migration',
        '版本': 'Version',
        '修订': 'Revision',
        '变更': 'Change',
        '修改': 'Modify',
        '编辑': 'Edit',
        '撤销': 'Undo',
        '重做': 'Redo',
        '历史': 'History',
        '审计': 'Audit',
        '跟踪': 'Trace',
        '监控': 'Monitor',
        '统计': 'Stats',
        '指标': 'Metric',
        '基准': 'Benchmark',
        '性能': 'Performance',
        '负载': 'Load',
        '压力': 'Stress',
        '测试': 'Test',
        '单元测试': 'UnitTest',
        '集成测试': 'IntegrationTest',
        '回归测试': 'RegressionTest',
        '冒烟测试': 'SmokeTest',
        '断言': 'Assert',
        '期望': 'Expect',
        '实际': 'Actual',
        '预期': 'Expected',
        '通过': 'Pass',
        '失败': 'Fail',
        '跳过': 'Skip',
        '忽略': 'Ignore',
        '套件': 'Suite',
        '固件': 'Fixture',
        '模拟': 'Mock',
        '桩': 'Stub',
        '假': 'Fake',
        '间谍': 'Spy',
        '代理': 'Proxy',
        '装饰器': 'Decorator',
        '适配器': 'Adapter',
        '工厂': 'Factory',
        '单例': 'Singleton',
        '观察者': 'Observer',
        '监听者': 'Listener',
        '订阅者': 'Subscriber',
        '发布者': 'Publisher',
        '调度器': 'Scheduler',
        '调度': 'Dispatch',
        '事件': 'Event',
        '消息': 'Message',
        '总线': 'Bus',
        '队列': 'Queue',
        '主题': 'Topic',
        '订阅': 'Subscribe',
        '发布': 'Publish',
        '通知': 'Notify',
        '回调': 'Callback',
        '钩子': 'Hook',
        '拦截器': 'Interceptor',
        '过滤器': 'Filter',
        '中间件': 'Middleware',
        '管道': 'Pipeline',
        '链': 'Chain',
        '责任链': 'ChainOfResponsibility',
        '命令模式': 'CommandPattern',
        '策略模式': 'StrategyPattern',
        '状态模式': 'StatePattern',
        '状态机': 'StateMachine',
        '有限状态机': 'FSM',
        '工作流': 'Workflow',
        '流程': 'Process',
        '步骤': 'Step',
        '阶段': 'Phase',
        '阶段': 'Stage',
        '里程碑': 'Milestone',
        '检查点': 'Checkpoint',
        '快照': 'Snapshot',
        '镜像': 'Image',
        '副本': 'Replica',
        '克隆': 'Clone',
        '复制': 'Copy',
        '移动': 'Move',
        '重命名': 'Rename',
        '归档': 'Archive',
        '压缩': 'Compress',
        '解压': 'Decompress',
        '打包': 'Package',
        '解包': 'Unpackage',
        '安装': 'Install',
        '卸载': 'Uninstall',
        '升级': 'Upgrade',
        '降级': 'Downgrade',
        '更新': 'Update',
        '补丁': 'Patch',
        '修复': 'Fix',
        '漏洞': 'Vulnerability',
        '安全': 'Security',
        '防护': 'Protection',
        '攻击': 'Attack',
        '防御': 'Defense',
        '加密': 'Encryption',
        '解密': 'Decryption',
        '签名': 'Signature',
        '证书': 'Certificate',
        '认证': 'Authentication',
        '授权': 'Authorization',
        '权限': 'Permission',
        '角色': 'Role',
        '组': 'Group',
        '访问控制': 'AccessControl',
        '令牌': 'Token',
        '票据': 'Ticket',
        '凭证': 'Credential',
        '凭据': 'Credential',
        '身份': 'Identity',
        '主体': 'Principal',
        '声明': 'Claim',
        '签发': 'Issue',
        '验证': 'Validate',
        '刷新': 'Refresh',
        '撤销': 'Revoke',
        '过期': 'Expire',
        '超时': 'Timeout',
        '刷新': 'Refresh',
        '续期': 'Renew',
        '注销': 'Logout',
        '登出': 'Logout',
        '退出': 'Exit',
        '退出登录': 'SignOut',
    }

    @classmethod
    def translate_comment(cls, comment: str) -> str:
        """翻译注释中的中文"""
        result = comment
        for chinese, english in cls.TERM_MAP.items():
            result = result.replace(chinese, english)
        return result

    @classmethod
    def translate_identifier(cls, identifier: str) -> str:
        """翻译标识符中的中文"""
        result = identifier
        for chinese, english in cls.TERM_MAP.items():
            if chinese in result:
                # 根据上下文决定大小写
                result = result.replace(chinese, english)
        return result


class CodeNormalizer:
    """代码规范化器"""

    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = {
        '.cpp', '.cxx', '.cc', '.c',
        '.h', '.hpp', '.hxx',
        '.py', '.pyw',
        '.java', '.kt',
        '.cs',
        '.js', '.ts',
        '.go', '.rs',
    }

    # 注释正则表达式
    COMMENT_PATTERNS = [
        # C/C++ 单行注释
        (re.compile(r'(//.*?)(\n|$)'), '//'),
        # C/C++ 多行注释
        (re.compile(r'/\*.*?\*/', re.DOTALL), '/* */'),
        # Python 单行注释
        (re.compile(r'(#.*?)(\n|$)'), '#'),
        # Python 多行注释（三引号）
        (re.compile(r'""".*?"""', re.DOTALL), '""" """'),
        (re.compile(r"'''.*?'''", re.DOTALL), "''' '''"),
    ]

    # 中文 Unicode 范围
    CHINESE_PATTERN = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002f800-\U0002fa1f]')

    def __init__(self, backup: bool = True):
        self.backup = backup
        self.mapper = ChineseToEnglishMapper()
        self.files_processed: List[str] = []
        self.files_modified: List[str] = []
        self.chinese_found: Dict[str, int] = {}

    def has_chinese(self, text: str) -> bool:
        """检查文本中是否包含中文"""
        return bool(self.CHINESE_PATTERN.search(text))

    def count_chinese(self, text: str) -> int:
        """统计中文汉字数量"""
        return len(self.CHINESE_PATTERN.findall(text))

    def process_file(self, file_path: Path) -> Tuple[bool, int, List[str]]:
        """处理单个文件

        Returns: (success, chinese_chars_removed, changes_made)
        """
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False, 0, []

        try:
            # 尝试多种编码读取
            content = None
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'latin1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                return False, 0, ['无法解码文件']

            original_chinese_count = self.count_chinese(content)

            if original_chinese_count == 0:
                self.files_processed.append(str(file_path))
                return True, 0, []

            changes_made = []
            modified_content = content

            # 1. 处理注释中的中文
            modified_content = self._process_comments(modified_content, changes_made)

            # 2. 处理字符串字面量中的中文（可选，默认不转换）
            # modified_content = self._process_strings(modified_content, changes_made)

            # 3. 处理标识符中的中文
            modified_content = self._process_identifiers(modified_content, changes_made)

            final_chinese_count = self.count_chinese(modified_content)
            chinese_removed = original_chinese_count - final_chinese_count

            if chinese_removed > 0:
                # 备份原文件
                if self.backup:
                    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                    shutil.copy2(file_path, backup_path)

                # 写入 UTF-8 BOM 编码（MSVC 友好）
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write(modified_content)

                self.files_modified.append(str(file_path))
                self.chinese_found[str(file_path)] = original_chinese_count

            self.files_processed.append(str(file_path))

            return True, chinese_removed, changes_made

        except Exception as e:
            return False, 0, [f'处理文件时出错: {str(e)}']

    def _process_comments(self, content: str, changes: List[str]) -> str:
        """处理注释中的中文"""
        # 简单处理：将所有注释中的中文翻译
        lines = content.split('\n')
        modified_lines = []

        for line in lines:
            # 检查是否是单行注释
            comment_start = -1

            # C/C++ 风格
            if '//' in line:
                comment_start = line.index('//')
            # Python 风格
            elif '#' in line:
                # 确保 # 不在字符串内（简化检查）
                if line.count('"') % 2 == 0 and line.count("'") % 2 == 0:
                    comment_start = line.index('#')

            if comment_start >= 0:
                code_part = line[:comment_start]
                comment_part = line[comment_start:]

                if self.has_chinese(comment_part):
                    translated = self.mapper.translate_comment(comment_part)
                    changes.append(f'翻译注释: {comment_part[:50]}...')
                    modified_lines.append(code_part + translated)
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)

        return '\n'.join(modified_lines)

    def _process_identifiers(self, content: str, changes: List[str]) -> str:
        """处理标识符中的中文"""
        # 查找可能是标识符的中文（变量名、函数名等）
        # 这是一个简化版本，实际需要更复杂的语法分析
        result = content

        # 查找中文单词并尝试翻译
        for match in self.CHINESE_PATTERN.finditer(content):
            chinese_char = match.group()
            # 这里简化处理：只替换常见词汇
            pass

        return result

    def process_directory(self, dir_path: Path, recursive: bool = True) -> Dict:
        """处理整个目录"""
        results = {
            'total_files': 0,
            'files_processed': 0,
            'files_modified': 0,
            'total_chinese_removed': 0,
            'files': []
        }

        if recursive:
            files = list(dir_path.rglob('*'))
        else:
            files = list(dir_path.iterdir())

        for file_path in files:
            if file_path.is_file():
                results['total_files'] += 1

                if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    success, chinese_removed, changes = self.process_file(file_path)
                    if success:
                        results['files_processed'] += 1
                        if chinese_removed > 0:
                            results['files_modified'] += 1
                            results['total_chinese_removed'] += chinese_removed
                            results['files'].append({
                                'file': str(file_path),
                                'chinese_removed': chinese_removed,
                                'changes': changes
                            })

        return results


class CodeNormalizerTool(BaseTool):
    """代码英文规范化工具"""

    name = "code_normalizer"
    description = "将代码中的中文注释和标识符转换为英文，防止 MSVC 编码错误 C4819"

    class Parameters(BaseModel):
        source_dir: str = Field(
            description="源代码目录路径"
        )
        backup: bool = Field(
            default=True,
            description="是否备份原文件（添加 .bak 后缀）"
        )
        convert_comments: bool = Field(
            default=True,
            description="是否转换注释中的中文"
        )
        convert_strings: bool = Field(
            default=False,
            description="是否转换字符串中的中文（不推荐，可能影响业务逻辑）"
        )
        remove_chinese_identifiers: bool = Field(
            default=True,
            description="是否转换标识符中的中文"
        )
        recursive: bool = Field(
            default=True,
            description="是否递归处理子目录"
        )
        file_extensions: Optional[str] = Field(
            default=None,
            description="指定要处理的文件扩展名，空格分隔，如 '.cpp .h'"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        source_path = Path(params.source_dir).resolve()

        if not source_path.exists():
            return ToolResult.error(f"源目录不存在: {source_path}")

        if source_path.is_file():
            # 处理单个文件
            normalizer = CodeNormalizer(backup=params.backup)
            success, chinese_removed, changes = normalizer.process_file(source_path)

            if success:
                if chinese_removed > 0:
                    return ToolResult.ok(
                        content=f"[OK] 文件处理完成\n"
                               f"     文件: {source_path.name}\n"
                               f"     移除中文字符数: {chinese_removed}\n"
                               f"     备份: {'已创建' if params.backup else '未创建'}",
                        chinese_removed=chinese_removed,
                        changes=changes,
                        file=str(source_path)
                    )
                else:
                    return ToolResult.ok(
                        content=f"[INFO] 文件不需要处理，未发现中文: {source_path.name}",
                        chinese_removed=0,
                        file=str(source_path)
                    )
            else:
                return ToolResult.error(
                    f"❌ 文件处理失败: {source_path.name}",
                    file=str(source_path),
                    errors=changes
                )
        else:
            # 处理整个目录
            normalizer = CodeNormalizer(backup=params.backup)
            results = normalizer.process_directory(source_path, params.recursive)

            if results['files_modified'] > 0:
                result_lines = [
                    "=" * 60,
                    "[OK] 代码规范化完成",
                    "=" * 60,
                    f"[DIR] 目录: {source_path}",
                    f"[TOTAL] 总文件数: {results['total_files']}",
                    f"[PROCESSED] 已处理: {results['files_processed']}",
                    f"[MODIFIED] 已修改: {results['files_modified']}",
                    f"[CHARS] 移除中文总数: {results['total_chinese_removed']}",
                    "",
                    "修改的文件:",
                ]

                for f in results['files'][:10]:
                    result_lines.append(
                        f"  - {Path(f['file']).name}: 移除 {f['chinese_removed']} 个中文字符"
                    )

                if len(results['files']) > 10:
                    result_lines.append(f"  还有 {len(results['files']) - 10} 个文件...")

                result_lines.append("=" * 60)

                return ToolResult.ok(
                    content='\n'.join(result_lines),
                    **results
                )
            else:
                return ToolResult.ok(
                    content=f"[INFO] 目录中未发现需要转换的中文代码\n"
                           f"[DIR] 目录: {source_path}\n"
                           f"[CHECKED] 已检查: {results['files_processed']} 个文件",
                    **results
                )
