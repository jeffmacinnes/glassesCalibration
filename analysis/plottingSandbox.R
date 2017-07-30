# overall Accuracy plot
library(ggplot2)
library(ggthemes)
library(ggpubr)

## Accuracy
accPlot <- ggplot(aes(y = centDist, x = glasses, fill=glasses), 
       data = dat) +
  geom_boxplot() +
  labs( 
    x = "Wearable Eye-tracker",
    y = "Visual Angle (deg)",
    title="Accuracy"
    ) +
  scale_fill_brewer(palette="Greens") +
  scale_y_continuous(breaks=seq(0,2,by=1), limits=c(0,2.5), expand=c(0,.1)) +
  theme(
    aspect.ratio = 1.5,
    panel.background = element_blank(),
    plot.title = element_text(hjust=.5, size=18),
    axis.title = element_text(size=rel(1.3)),
    axis.text.x = element_text(size = rel(1.3)),
    axis.text.y = element_text(size = rel(1.5)),
    axis.line.y = element_line(colour = "black", size = .5, linetype = "solid"),
    axis.ticks.x = element_blank(),
    panel.grid.major.y = element_line(colour="darkgrey", linetype = "twodash", size=.25),
    legend.position = "none",
  ) +
  geom_segment(aes(x = .4, y = 0, xend = 3.6, yend = 0), size=.25)


## Precision
rmsPlot <- ggplot(aes(y = RMS, x = glasses, fill=glasses), 
                  data = dat) +
  geom_boxplot() +
  labs( 
    x = "Wearable Eye-tracker",
    y = "RMS",
    title="Precision"
  ) +
  scale_fill_brewer(palette="Greens") +
  scale_y_continuous(breaks=seq(0,.8,by=.2), limits=c(0,.7), expand=c(0,.03)) +
  theme(
    aspect.ratio = 1.5,
    panel.background = element_blank(),
    plot.title = element_text(hjust=.5, size=18),
    axis.title = element_text(size=rel(1.3)),
    axis.text.x = element_text(size = rel(1.3)),
    axis.text.y = element_text(size = rel(1.5)),
    axis.line.y = element_line(colour = "black", size = .5, linetype = "solid"),
    axis.ticks.x = element_blank(),
    panel.grid.major.y = element_line(colour="darkgrey", linetype = "twodash", size=.25),
    legend.position = "none",
  ) +
  geom_segment(aes(x = .4, y = 0, xend = 3.6, yend = 0), size=.25)

rmsPlot
  
## Combine plots
ggarrange(accPlot, rmsPlot,  
          labels = c("A", "B"),
          ncol = 2, nrow = 1) + 
  ggsave("figs/overallAccPrec.pdf", width = 8, height = 5)
