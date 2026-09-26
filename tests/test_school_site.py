# -*- coding: utf-8 -*-
"""学校网站保护: 域名匹配/系统代理接管判定/Clash 连接解析。"""

from campus_proxy_guard.detector import (
    domain_matches,
    parse_clash_connections,
    school_domains_at_risk,
)

DOMAINS = ["jxufe.edu.cn"]


class TestDomainMatches:
    def test_exact(self):
        assert domain_matches("jxufe.edu.cn", DOMAINS)

    def test_subdomain(self):
        assert domain_matches("www.jxufe.edu.cn", DOMAINS)
        assert domain_matches("lib.jxufe.edu.cn.", DOMAINS)  # 尾点

    def test_case_insensitive(self):
        assert domain_matches("WWW.JXUFE.EDU.CN", DOMAINS)

    def test_wildcard_pattern(self):
        assert domain_matches("a.jxufe.edu.cn", ["*.jxufe.edu.cn"])

    def test_suffix_lookalike_rejected(self):
        # "eviljxufe.edu.cn" 不是 "jxufe.edu.cn" 的子域
        assert not domain_matches("eviljxufe.edu.cn", DOMAINS)

    def test_unrelated_rejected(self):
        assert not domain_matches("example.com", DOMAINS)

    def test_empty_patterns(self):
        assert not domain_matches("jxufe.edu.cn", [])


class TestSchoolDomainsAtRisk:
    def test_proxy_off_no_risk(self):
        assert school_domains_at_risk(False, "", DOMAINS) == []

    def test_no_bypass_all_risky(self):
        assert school_domains_at_risk(True, "", DOMAINS) == DOMAINS

    def test_exact_bypass(self):
        assert school_domains_at_risk(True, "jxufe.edu.cn", DOMAINS) == []

    def test_wildcard_bypass(self):
        assert school_domains_at_risk(True, "*.jxufe.edu.cn;localhost", DOMAINS) == []

    def test_partial_bypass(self):
        domains = ["jxufe.edu.cn", "example.edu.cn"]
        assert school_domains_at_risk(True, "example.edu.cn", domains) == ["jxufe.edu.cn"]


CLASH_SAMPLE = {
    "connections": [
        {"metadata": {"host": "www.jxufe.edu.cn", "destinationIP": "202.101.1.1",
                      "network": "tcp"}},
        {"metadata": {"host": "github.com", "destinationIP": "140.82.1.1"}},
        {"metadata": {"host": "", "sniffHost": "lib.jxufe.edu.cn"}},
        {"metadata": {"host": "portal.jxufe.edu.cn", "destinationIP": "portal.jxufe.edu.cn"}},
    ],
}


class TestParseClashConnections:
    def test_finds_school_connections(self):
        matched = parse_clash_connections(CLASH_SAMPLE, DOMAINS)
        assert "www.jxufe.edu.cn(202.101.1.1)" in matched
        assert "lib.jxufe.edu.cn" in matched
        # destinationIP 与 host 相同时不重复标注
        assert "portal.jxufe.edu.cn" in matched
        assert not any("github" in m for m in matched)

    def test_empty_connections(self):
        assert parse_clash_connections({"connections": None}, DOMAINS) == []
        assert parse_clash_connections({}, DOMAINS) == []

    def test_malformed_entries_skipped(self):
        data = {"connections": ["garbage", 42, {"metadata": None}]}
        assert parse_clash_connections(data, DOMAINS) == []


def test_check_school_sites_no_domains():
    """未配置学校域名时恒为空。"""
    from campus_proxy_guard.config import Config
    from campus_proxy_guard.detector import check_school_sites

    cfg = Config()
    cfg.school_domains = []
    assert check_school_sites(cfg) == []
