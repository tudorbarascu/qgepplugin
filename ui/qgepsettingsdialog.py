# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# Profile
# Copyright (C) 2012  Matthias Kuhn
# -----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, print to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# ---------------------------------------------------------------------

from ui_qgepsettingsdialog import Ui_QgepSettingsDialog
from PyQt4.QtCore import QSettings, pyqtSlot
from PyQt4.QtGui import QDialog, QFileDialog, QColor
from qgis.core import QgsMapLayerRegistry, QgsProject
import logging

LOGFORMAT = '%(asctime)s:%(levelname)s:%(module)s:%(message)s'


class QgepSettingsDialog(QDialog, Ui_QgepSettingsDialog):
    settings = QSettings()

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        project = QgsProject.instance()

        svgprofile_path = self.settings.value("/QGEP/SvgProfilePath", None)
        if svgprofile_path:
            self.mGbOverrideDefaultProfileTemplate.setChecked(True)
            self.mProfileTemplateFile.setText(svgprofile_path)
        else:
            self.mGbOverrideDefaultProfileTemplate.setChecked(False)

        develmode = self.settings.value("/QGEP/DeveloperMode", False, type=bool)
        self.mCbDevelMode.setChecked(develmode)

        lyrSpecialStructures, _ = project.readEntry('QGEP', 'SpecialStructureLayer')
        lyrGraphEdges, _ = project.readEntry('QGEP', 'GraphEdgeLayer')
        lyrGraphNodes, _ = project.readEntry('QGEP', 'GraphNodeLayer')

        self.initLayerCombobox(self.mCbSpecialStructures, lyrSpecialStructures)
        self.initLayerCombobox(self.mCbGraphEdges, lyrGraphEdges)
        self.initLayerCombobox(self.mCbGraphNodes, lyrGraphNodes)

        self.mCurrentProfileColorButton.setColor(QColor(self.settings.value("/QGEP/CurrentProfileColor", u'#FF9500')))
        self.mHelperLineColorButton.setColor(QColor(self.settings.value("/QGEP/HelperLineColor", u'#FFD900')))
        self.mHighlightColorButton.setColor(QColor(self.settings.value("/QGEP/HighlightColor", u'#40FF40')))

        self.mPbnChooseProfileTemplateFile.clicked.connect(self.onChooseProfileTemplateFileClicked)
        self.mPbnChooseLogFile.clicked.connect(self.onChooseLogFileClicked)

        self.accepted.connect(self.onAccept)

        loglevel = self.settings.value("/QGEP/LogLevel", 'Warning')
        self.mCbLogLevel.setCurrentIndex(self.mCbLogLevel.findText(self.tr(loglevel)))

        logfile = self.settings.value("/QGEP/LogFile", None)

        if logfile is not None:
            self.mGbLogToFile.setChecked(True)
            self.mLogFile.setText(logfile)
        else:
            self.mGbLogToFile.setChecked(False)

    def initLayerCombobox(self, combobox, default):
        reg = QgsMapLayerRegistry.instance()
        for (key, layer) in reg.mapLayers().iteritems():
            combobox.addItem(layer.name(), key)

        idx = combobox.findData(default)
        if idx != -1:
            combobox.setCurrentIndex(idx)

    @pyqtSlot()
    def onAccept(self):
        qgeplogger = logging.getLogger('qgep')
        # General settings
        if self.mGbOverrideDefaultProfileTemplate.isChecked() \
                and self.mProfileTemplateFile.text():
            self.settings.setValue("/QGEP/SvgProfilePath", self.mProfileTemplateFile.text())
        else:
            self.settings.remove("/QGEP/SvgProfilePath")

        self.settings.setValue("/QGEP/DeveloperMode", self.mCbDevelMode.checkState())

        # Logging
        if hasattr(qgeplogger, 'qgepFileHandler'):
            qgeplogger.removeHandler(qgeplogger.qgepFileHandler)
            del qgeplogger.qgepFileHandler

        if self.mGbLogToFile.isChecked():
            logfile = unicode(self.mLogFile.text())
            log_handler = logging.FileHandler(logfile)
            fmt = logging.Formatter(LOGFORMAT)
            log_handler.setFormatter(fmt)
            qgeplogger.addHandler(log_handler)
            qgeplogger.qgepFileHandler = log_handler
            self.settings.setValue("/QGEP/LogFile", logfile)
        else:
            self.settings.setValue("/QGEP/LogFile", None)

        if self.tr('Debug') == self.mCbLogLevel.currentText():
            qgeplogger.setLevel(logging.DEBUG)
            self.settings.setValue("/QGEP/LogLevel", 'Debug')
        elif self.tr('Info') == self.mCbLogLevel.currentText():
            qgeplogger.setLevel(logging.INFO)
            self.settings.setValue("/QGEP/LogLevel", 'Info')
        elif self.tr('Warning') == self.mCbLogLevel.currentText():
            qgeplogger.setLevel(logging.WARNING)
            self.settings.setValue("/QGEP/LogLevel", 'Warning')
        elif self.tr('Error') == self.mCbLogLevel.currentText():
            qgeplogger.setLevel(logging.ERROR)
            self.settings.setValue("/QGEP/LogLevel", 'Error')

        # Save colors
        self.settings.setValue("/QGEP/HelperLineColor", self.mHelperLineColorButton.color().name())
        self.settings.setValue("/QGEP/HighlightColor", self.mHighlightColorButton.color().name())
        self.settings.setValue("/QGEP/CurrentProfileColor", self.mCurrentProfileColorButton.color().name())

        # Project specific settings
        project = QgsProject.instance()

        specialstructure_idx = self.mCbSpecialStructures.currentIndex()
        graph_edgelayer_idx = self.mCbGraphEdges.currentIndex()
        graph_nodelayer_idx = self.mCbGraphNodes.currentIndex()

        project.writeEntry('QGEP', 'SpecialStructureLayer', self.mCbSpecialStructures.itemData(specialstructure_idx))
        project.writeEntry('QGEP', 'GraphEdgeLayer', self.mCbGraphEdges.itemData(graph_edgelayer_idx))
        project.writeEntry('QGEP', 'GraphNodeLayer', self.mCbGraphNodes.itemData(graph_nodelayer_idx))

    @pyqtSlot()
    def onChooseProfileTemplateFileClicked(self):
        filename = QFileDialog.getOpenFileName(self, self.tr('Select profile template'), '',
                                               self.tr('HTML files(*.htm *.html)'))
        self.mProfileTemplateFile.setText(filename)

    @pyqtSlot()
    def onChooseLogFileClicked(self):
        filename = QFileDialog.getSaveFileName(self, self.tr('Select log file'), '', self.tr('Log files(*.log)'))
        self.mLogFile.setText(filename)
