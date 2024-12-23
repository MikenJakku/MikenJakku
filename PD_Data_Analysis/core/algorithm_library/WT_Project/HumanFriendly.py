#! /bin/bash/env python
# -*- coding: utf-8 -*-
# ===== compiler flag =====
# distutils: language = c++
# cython: language_level = 3
# ===== compiler flag =====


class HumanFriendly:
    # 诊断、健康评级等结果的自然语言描述，用于分析报告。
    def __init__(self, pos, results, health_status_mapping, position_mapping, wave_comment_mapping, defect_freq_mapping,
                 spec_comment_mapping, trending_comment_mapping, statistic_NL_mapping, rotational_defects_mapping,
                 defect_level_mapping, maintenance_NL_mapping):
        self.pos = pos
        self.rst = results
        if "trending" in self.rst.keys():
            self.trending = self.rst["trending"]
        else:
            self.health_status = self.rst["health_status"]["status"]
            self.if_shock = self.rst["shock"]["if_shock"]
            self.shock_snr = self.rst["shock"]["shock_snr"]
            self.diagnosis_rst = self.rst["diagnosis_rst"]

        self.health_status_mapping = health_status_mapping
        self.position_mapping = position_mapping
        self.wave_comment_mapping = wave_comment_mapping
        self.defect_freq_mapping = defect_freq_mapping
        self.spec_comment_mapping = spec_comment_mapping
        self.trending_comment_mapping = trending_comment_mapping
        self.statistic_NL_mapping = statistic_NL_mapping
        self.rotational_defects_mapping = rotational_defects_mapping
        self.defect_level_mapping = defect_level_mapping
        self.maintenance_NL_mapping = maintenance_NL_mapping

    def health_stat_NL(self):
        return self.health_status_mapping[self.health_status]

    def waveform_NL(self):
        if self.if_shock:
            state = self.wave_comment_mapping["ValidatingData"]
        else:
            state = self.wave_comment_mapping["0"]

        full_state = self.position_mapping[self.pos] + state

        return full_state

    def spec_NL(self):
        pos_com = self.position_mapping[self.pos]
        comment = []
        if self.diagnosis_rst == {}:
            state = self.spec_comment_mapping["0"]
            full_state = pos_com + state
            comment.append(full_state)
        else:
            for key, values in self.diagnosis_rst.items():
                state = self.spec_comment_mapping["ValidatingData"]
                kind = self.defect_freq_mapping[key]
                full_state = pos_com + "可见" + kind + state
                comment.append(full_state)

        return comment

    def trending_NL(self):
        comment = []
        for feature, trend in self.trending.items():
            ft_com = self.statistic_NL_mapping[feature]
            if trend:
                state = self.trending_comment_mapping["ValidatingData"]
            else:
                state = self.trending_comment_mapping["0"]

            full_comm = ft_com + state

            comment.append(full_comm)

        return comment

    def diagn_mainten_NL(self):

        pos_com = self.position_mapping[self.pos]

        score = 0

        com = []
        # 冲击特征
        if self.if_shock:
            shock_state = self.wave_comment_mapping["ValidatingData"]
            if self.shock_snr >= 30:
                score += 3
            elif self.shock_snr >= 10:
                score += 2
            else:
                score += 1
        else:
            shock_state = self.wave_comment_mapping["0"]
        full_state = pos_com + shock_state
        com.append(full_state)

        # 谐波缺陷

        if self.diagnosis_rst == {}:
            spec_stat = self.spec_comment_mapping["0"]
            full_stat = pos_com + spec_stat
            com.append(full_stat)
        else:
            lev = []
            for ft, values in self.diagnosis_rst.items():
                lev_state = self.defect_level_mapping[values["level"]]
                lev.append(values['level'])

                if ft == 'rotation':
                    defect_state = ''
                    for i in values["defect"]:
                        defect_state = defect_state + self.rotational_defects_mapping[i] + '、'
                    defect_state = defect_state[:-1]
                    full_state = pos_com + "可能存在" + defect_state + "等缺陷。"
                else:
                    loc_state = self.defect_freq_mapping[ft]
                    full_state = pos_com + loc_state + "存在" + lev_state + "表面损伤。"
                com.append(full_state)

            if "vital" in lev:
                score += 3
            elif "obvious" in lev:
                score += 2
            elif "slight" in lev:
                score += 1
            else:
                pass

        if score >= 5:
            man_state = self.maintenance_NL_mapping["3"]
        elif 5 > score >= 3:
            man_state = self.maintenance_NL_mapping["2"]
        elif 3 > score >= 1:
            man_state = self.maintenance_NL_mapping["ValidatingData"]
        else:
            man_state = self.maintenance_NL_mapping["0"]

        return com, man_state

    def nature_language(self):
        if "trending" in self.rst.keys():
            trending = self.trending_NL()
            return {"trendingNL": trending}
        else:
            health_stat = self.health_stat_NL()
            waveform = self.waveform_NL()
            spectrum = self.spec_NL()
            #
            diagnosis, maintenance = self.diagn_mainten_NL()

            rst = {
                "health_statNL": health_stat,
                "waveformNL": waveform,
                "spectrumNL": spectrum,
                "diagnosisNL": diagnosis,
                "maintenanceNL": maintenance
            }

            return rst
