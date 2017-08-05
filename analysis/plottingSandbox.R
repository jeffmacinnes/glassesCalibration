# overall Accuracy plot
library(ggplot2)
library(ggthemes)
library(ggpubr)

## Accuracy
ggplot(aes(y = centDist, x = dist, fill=glasses), 
       data = dat) +
  geom_boxplot(width=.69, position=position_dodge(.74), 
               outlier.colour = NULL, aes_string(colour="glasses")) +
  stat_summary(geom="crossbar", width=.65, fatten=1, color="white",
               fun.data = function(x){ return(c(y=median(x), ymin=median(x), ymax=median(x))) },
               position=position_dodge(.74)) +
  labs( 
    x = "Distance (m)",
    y = "Visual Angle (deg)",
    title="Accuracy"
    ) +
  scale_fill_manual("eye-tracker", values=c("#FC940A", "#DD5431", "#4A3223")) +
  scale_colour_manual("eye-tracker", values=c("#FC940A", "#DD5431", "#4A3223")) + 
  scale_y_continuous(breaks=seq(0,2,by=1), limits=c(0,2.5), expand=c(0,.1)) +
  scale_x_discrete(breaks = c("1M", "2M", "3M"), labels=c("1", "2", "3")) +
  theme(
    aspect.ratio = .6,
    panel.background = element_blank(),
    plot.title = element_text(hjust=.5, size=18),
    axis.title = element_text(size=rel(1.3)),
    axis.text.x = element_text(size = rel(1.5)),
    axis.text.y = element_text(size = rel(1.5)),
    axis.line.y = element_line(colour = "black", size = .5, linetype = "solid"),
    axis.ticks.x = element_blank(),
    panel.grid.major.y = element_line(colour="grey80", linetype = "twodash", size=.25),
    legend.key.size = unit(2,"line"),
    legend.key = element_blank(),
    legend.title = element_text(face="bold")
    ) +
  geom_segment(aes(x = .4, y = 0, xend = 3.6, yend = 0), size=.25) +

  ## significance annotations
  geom_signif(y_position=2.35, xmin=2.77, xmax=3.23, annotation="***", tip_length=0.01, size=1) +
  geom_signif(y_position=2.15, xmin=3, xmax=3.23, annotation="*", tip_length=0.01, size=1) +
  geom_signif(y_position=1.75, xmin=2.77, xmax=3, annotation="0.06", tip_length=0.01) + 
  geom_signif(y_position=2.35, xmin=1.77, xmax=2.23, annotation="0.06", tip_length=0.01) +
  
  ## save
  ggsave("figs/ACC_glasses_by_dist.pdf", width = 8, height = 5)

# ## Precision
# rmsPlot <- ggplot(aes(y = RMS, x = glasses, fill=glasses), 
#                   data = dat) +
#   geom_boxplot() +
#   labs( 
#     x = "Wearable Eye-tracker",
#     y = "RMS",
#     title="Precision"
#   ) +
#   scale_fill_brewer(palette="Greens") +
#   scale_y_continuous(breaks=seq(0,.8,by=.2), limits=c(0,.7), expand=c(0,.03)) +
#   theme(
#     aspect.ratio = 1.5,
#     panel.background = element_blank(),
#     plot.title = element_text(hjust=.5, size=18),
#     axis.title = element_text(size=rel(1.3)),
#     axis.text.x = element_text(size = rel(1.3)),
#     axis.text.y = element_text(size = rel(1.5)),
#     axis.line.y = element_line(colour = "black", size = .5, linetype = "solid"),
#     axis.ticks.x = element_blank(),
#     panel.grid.major.y = element_line(colour="darkgrey", linetype = "twodash", size=.25),
#     legend.position = "none",
#   ) +
#   geom_segment(aes(x = .4, y = 0, xend = 3.6, yend = 0), size=.25)
# 
# rmsPlot
#   
# ## Combine plots
# ggarrange(accPlot, rmsPlot,  
#           labels = c("A", "B"),
#           ncol = 2, nrow = 1) + 
#   ggsave("figs/overallAccPrec.pdf", width = 8, height = 5)
